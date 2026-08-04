from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: Literal["local", "openai", "deepgram", "assemblyai", "adapted"]
    ready: bool
    reason: str | None = None
    size_hint: str | None = None
    base_model: str | None = None
    adapter_path: str | None = None


class TranscriptResult(BaseModel):
    model_id: str
    model_name: str
    provider: str
    transcript: str
    latency_ms: float
    audio_duration_sec: float | None = None
    rtf: float | None = None
    wer: float | None = None
    cer: float | None = None
    error: str | None = None
    words: list[str] = Field(default_factory=list)
    diff_ops: list[dict[str, Any]] = Field(default_factory=list)


class TranscribeResponse(BaseModel):
    run_id: str
    audio_path: str
    audio_duration_sec: float | None
    reference: str | None
    results: list[TranscriptResult]


class EvaluateSampleResult(BaseModel):
    sample_id: str
    reference: str
    base_transcript: str
    adapted_transcript: str | None = None
    base_wer: float | None = None
    adapted_wer: float | None = None
    base_cer: float | None = None
    adapted_cer: float | None = None


class EvaluateResponse(BaseModel):
    id: str
    dataset_id: str
    base_model: str
    adapter_id: str | None
    split: str
    sample_count: int
    base_wer: float | None
    adapted_wer: float | None
    delta_wer: float | None
    base_cer: float | None
    adapted_cer: float | None
    delta_cer: float | None
    samples: list[EvaluateSampleResult]
