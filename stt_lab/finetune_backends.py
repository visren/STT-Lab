"""Fine-tune backends: local (default) and cloud (pluggable).

Local runs PEFT LoRA in-process via ``services.finetune``.
Cloud backends should upload the dataset + recipe and return a job id that
polls into the same ``FinetuneJob`` rows / ``data/adapters/`` layout.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from sqlalchemy.orm import Session

from .db import FinetuneJob
from .services.finetune import start_finetune_job


BackendName = Literal["local", "cloud"]


class FinetuneBackend(ABC):
    name: str

    @abstractmethod
    def start(self, db: Session, job: FinetuneJob) -> None:
        ...


class LocalFinetuneBackend(FinetuneBackend):
    name = "local"

    def start(self, db: Session, job: FinetuneJob) -> None:
        start_finetune_job(db, job)


class CloudFinetuneBackend(FinetuneBackend):
    """Placeholder for Modal / HF Jobs / RunPod.

    Wire a real provider by implementing dataset upload + remote train that
    writes the resulting adapter under ``data/adapters/{job_id}`` and updates
    the job row status/progress/logs.
    """

    name = "cloud"

    def start(self, db: Session, job: FinetuneJob) -> None:
        from .config import settings
        from .db import utcnow
        from .services.finetune import append_log, update_job

        if not settings.cloud_finetune_backend:
            update_job(
                db,
                job,
                status="failed",
                error=(
                    "Cloud fine-tune is not configured. Set CLOUD_FINETUNE_BACKEND "
                    "(modal|hf_jobs|runpod) and CLOUD_FINETUNE_TOKEN in .env, then "
                    "implement the provider hook in stt_lab/finetune_backends.py."
                ),
            )
            append_log(db, job, "Cloud backend not configured")
            return

        update_job(db, job, status="failed", error="Cloud backend not implemented yet")
        append_log(
            db,
            job,
            (
                f"Requested cloud backend '{settings.cloud_finetune_backend}' — "
                "implementation pending. Use backend='local' for now."
            ),
        )
        job.updated_at = utcnow()
        db.commit()


def get_backend(name: BackendName = "local") -> FinetuneBackend:
    if name == "local":
        return LocalFinetuneBackend()
    if name == "cloud":
        return CloudFinetuneBackend()
    raise ValueError(f"Unknown fine-tune backend: {name}")
