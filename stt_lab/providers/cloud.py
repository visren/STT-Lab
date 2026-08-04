from __future__ import annotations

import asyncio
import time
from pathlib import Path

from ..config import settings
from .base import ProviderResult, STTProvider


class OpenAIProvider(STTProvider):
    def __init__(self):
        self.id = "openai-whisper-1"
        self.name = "OpenAI Whisper"
        self.provider = "openai"

    def ready(self) -> tuple[bool, str | None]:
        if not settings.openai_api_key:
            return False, "OPENAI_API_KEY not configured"
        return True, None

    def _transcribe_sync(self, audio_path: str, language: str | None) -> ProviderResult:
        started = time.perf_counter()
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            with open(audio_path, "rb") as f:
                kwargs = {"model": "whisper-1", "file": f}
                if language:
                    kwargs["language"] = language
                resp = client.audio.transcriptions.create(**kwargs)
            text = (getattr(resp, "text", None) or str(resp)).strip()
            return ProviderResult(
                transcript=text, latency_ms=(time.perf_counter() - started) * 1000
            )
        except Exception as exc:
            return ProviderResult(
                transcript="",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )

    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)


class DeepgramProvider(STTProvider):
    def __init__(self):
        self.id = "deepgram-nova-2"
        self.name = "Deepgram Nova-2"
        self.provider = "deepgram"

    def ready(self) -> tuple[bool, str | None]:
        if not settings.deepgram_api_key:
            return False, "DEEPGRAM_API_KEY not configured"
        return True, None

    def _transcribe_sync(self, audio_path: str, language: str | None) -> ProviderResult:
        started = time.perf_counter()
        try:
            from deepgram import DeepgramClient, PrerecordedOptions, FileSource

            client = DeepgramClient(settings.deepgram_api_key)
            with open(audio_path, "rb") as f:
                payload: FileSource = {"buffer": f.read()}
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language=language or "en",
            )
            response = client.listen.rest.v("1").transcribe_file(payload, options)
            alt = response.results.channels[0].alternatives[0]
            text = (alt.transcript or "").strip()
            return ProviderResult(
                transcript=text, latency_ms=(time.perf_counter() - started) * 1000
            )
        except Exception as exc:
            return ProviderResult(
                transcript="",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )

    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)


class AssemblyAIProvider(STTProvider):
    def __init__(self):
        self.id = "assemblyai-best"
        self.name = "AssemblyAI Best"
        self.provider = "assemblyai"

    def ready(self) -> tuple[bool, str | None]:
        if not settings.assemblyai_api_key:
            return False, "ASSEMBLYAI_API_KEY not configured"
        return True, None

    def _transcribe_sync(self, audio_path: str, language: str | None) -> ProviderResult:
        started = time.perf_counter()
        try:
            import assemblyai as aai

            aai.settings.api_key = settings.assemblyai_api_key
            config = aai.TranscriptionConfig(language_code=language or "en")
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(str(Path(audio_path).resolve()))
            if transcript.status == aai.TranscriptStatus.error:
                raise RuntimeError(transcript.error or "AssemblyAI transcription failed")
            text = (transcript.text or "").strip()
            return ProviderResult(
                transcript=text, latency_ms=(time.perf_counter() - started) * 1000
            )
        except Exception as exc:
            return ProviderResult(
                transcript="",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )

    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path, language)
