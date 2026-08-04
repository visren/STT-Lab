from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ..config import ADAPTERS_DIR
from ..db import FinetuneJob
from ..models import ModelInfo
from .base import STTProvider
from .cloud import AssemblyAIProvider, DeepgramProvider, OpenAIProvider
from .local_whisper import AdaptedWhisperProvider, FasterWhisperProvider, WHISPER_SIZES


def built_in_providers() -> list[STTProvider]:
    locals_ = [FasterWhisperProvider(size) for size in WHISPER_SIZES]
    clouds = [OpenAIProvider(), DeepgramProvider(), AssemblyAIProvider()]
    return [*locals_, *clouds]


def adapted_providers(db: Session) -> list[AdaptedWhisperProvider]:
    jobs = (
        db.query(FinetuneJob)
        .filter(FinetuneJob.status == "completed", FinetuneJob.adapter_path.isnot(None))
        .order_by(FinetuneJob.updated_at.desc())
        .all()
    )
    providers: list[AdaptedWhisperProvider] = []
    for job in jobs:
        if not job.adapter_path or not Path(job.adapter_path).exists():
            continue
        # Stub cloud adapters are lifecycle markers, not loadable PEFT weights.
        if (Path(job.adapter_path) / "STUB_ADAPTER.json").exists():
            continue
        providers.append(
            AdaptedWhisperProvider(
                adapter_id=job.id,
                base_model=job.base_model,
                adapter_path=job.adapter_path,
                name=f"Adapted {job.base_model} ({job.id[:8]})",
            )
        )
    return providers


def list_models(db: Session) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    for p in built_in_providers():
        ready, reason = p.ready()
        models.append(
            ModelInfo(
                id=p.id,
                name=p.name,
                provider=p.provider,  # type: ignore[arg-type]
                ready=ready,
                reason=reason,
                size_hint=getattr(p, "size", None),
            )
        )
    for p in adapted_providers(db):
        ready, reason = p.ready()
        models.append(
            ModelInfo(
                id=p.id,
                name=p.name,
                provider="adapted",
                ready=ready,
                reason=reason,
                base_model=p.base_model,
                adapter_path=p.adapter_path,
            )
        )
    return models


def get_providers_by_ids(db: Session, model_ids: list[str]) -> list[STTProvider]:
    all_providers: dict[str, STTProvider] = {p.id: p for p in built_in_providers()}
    for p in adapted_providers(db):
        all_providers[p.id] = p
    missing = [mid for mid in model_ids if mid not in all_providers]
    if missing:
        raise ValueError(f"Unknown model ids: {', '.join(missing)}")
    return [all_providers[mid] for mid in model_ids]


def adapter_dir_for(job_id: str) -> Path:
    path = ADAPTERS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path
