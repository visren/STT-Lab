from __future__ import annotations

import asyncio
import time
from functools import lru_cache

from ..config import settings
from .base import ProviderResult, STTProvider

WHISPER_SIZES = ("tiny", "base", "small", "medium")


def resolve_device() -> str:
    choice = (settings.whisper_device or "auto").lower()
    if choice != "auto":
        return choice
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            # faster-whisper uses CTranslate2; MPS not supported — fall back to CPU
            return "cpu"
    except Exception:
        pass
    return "cpu"


def resolve_compute_type(device: str) -> str:
    if device == "cuda":
        return "float16"
    return "int8"


@lru_cache(maxsize=4)
def _load_model(size: str):
    from faster_whisper import WhisperModel

    device = resolve_device()
    compute_type = resolve_compute_type(device)
    return WhisperModel(size, device=device, compute_type=compute_type)


class FasterWhisperProvider(STTProvider):
    def __init__(self, size: str):
        if size not in WHISPER_SIZES:
            raise ValueError(f"Unsupported Whisper size: {size}")
        self.size = size
        self.id = f"whisper-{size}"
        self.name = f"Whisper {size}"
        self.provider = "local"

    def ready(self) -> tuple[bool, str | None]:
        return True, None

    def _transcribe_sync(self, audio_path: str, language: str | None) -> ProviderResult:
        started = time.perf_counter()
        try:
            model = _load_model(self.size)
            segments, _info = model.transcribe(
                audio_path,
                language=language or None,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            latency_ms = (time.perf_counter() - started) * 1000
            return ProviderResult(transcript=text, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return ProviderResult(transcript="", latency_ms=latency_ms, error=str(exc))

    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)


class AdaptedWhisperProvider(STTProvider):
    """Inference via transformers + PEFT adapter (for fine-tuned models)."""

    def __init__(self, adapter_id: str, base_model: str, adapter_path: str, name: str | None = None):
        self.adapter_id = adapter_id
        self.base_model = base_model
        self.adapter_path = adapter_path
        self.id = f"adapted-{adapter_id}"
        self.name = name or f"Adapted Whisper {base_model}"
        self.provider = "adapted"
        self._pipe = None

    def ready(self) -> tuple[bool, str | None]:
        from pathlib import Path

        if not Path(self.adapter_path).exists():
            return False, "Adapter not found"
        return True, None

    def _get_pipe(self):
        if self._pipe is not None:
            return self._pipe
        import torch
        from peft import PeftModel
        from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline

        hf_id = f"openai/whisper-{self.base_model}"
        device = resolve_device()
        if device == "mps":
            torch_device = "mps"
        elif device == "cuda":
            torch_device = "cuda"
        else:
            torch_device = "cpu"

        processor = WhisperProcessor.from_pretrained(hf_id)
        model = WhisperForConditionalGeneration.from_pretrained(hf_id)
        model = PeftModel.from_pretrained(model, self.adapter_path)
        model.eval()
        self._pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            device=0 if torch_device == "cuda" else torch_device,
            chunk_length_s=30,
        )
        return self._pipe

    def _transcribe_sync(self, audio_path: str, language: str | None) -> ProviderResult:
        started = time.perf_counter()
        try:
            pipe = self._get_pipe()
            generate_kwargs = {}
            if language:
                generate_kwargs["language"] = language
            out = pipe(audio_path, generate_kwargs=generate_kwargs or None)
            text = (out.get("text") if isinstance(out, dict) else str(out) or "").strip()
            latency_ms = (time.perf_counter() - started) * 1000
            return ProviderResult(transcript=text, latency_ms=latency_ms)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return ProviderResult(transcript="", latency_ms=latency_ms, error=str(exc))

    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)
