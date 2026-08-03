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


class DatasetCreate(BaseModel):
    name: str
    description: str = ""


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SampleUpdate(BaseModel):
    transcript: str | None = None
    split: Literal["train", "val"] | None = None


class SampleOut(BaseModel):
    id: str
    dataset_id: str
    audio_path: str
    transcript: str
    split: str
    duration_sec: float | None
    created_at: str


class DatasetOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    sample_count: int
    train_count: int
    val_count: int
    samples: list[SampleOut] = Field(default_factory=list)


class FinetuneRequest(BaseModel):
    dataset_id: str
    base_model: Literal["tiny", "base", "small", "medium"] = "tiny"
    lora_rank: int = 16
    lora_alpha: int = 32
    learning_rate: float = 1e-4
    epochs: int = 3
    batch_size: int = 1
    language: str = "en"


class FinetuneJobOut(BaseModel):
    id: str
    dataset_id: str
    base_model: str
    status: str
    progress: float
    logs: str
    adapter_path: str | None
    error: str | None
    config: dict[str, Any]
    created_at: str
    updated_at: str
    cancelled: bool


class EvaluateRequest(BaseModel):
    dataset_id: str
    base_model: Literal["tiny", "base", "small", "medium"] = "tiny"
    adapter_id: str | None = None
    split: Literal["train", "val"] = "val"


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


class SettingsOut(BaseModel):
    openai_configured: bool
    deepgram_configured: bool
    assemblyai_configured: bool
    whisper_device: str
    data_dir: str


class SettingsUpdate(BaseModel):
    openai_api_key: str | None = None
    deepgram_api_key: str | None = None
    assemblyai_api_key: str | None = None
    whisper_device: str | None = None
