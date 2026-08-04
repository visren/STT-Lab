"""Fine-tune backends: local (default) and cloud (pluggable providers).

Local runs PEFT LoRA in-process via ``services.finetune``.
Cloud uses ``stt_lab.cloud_finetune`` providers; ``stub`` exercises the full
upload → poll → download lifecycle without a real GPU service.
"""

from __future__ import annotations

import json
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from sqlalchemy.orm import Session

from .config import ADAPTERS_DIR, DATASETS_DIR, ensure_dirs
from .db import FinetuneJob, Sample, SessionLocal
from .services.finetune import append_log, start_finetune_job, update_job


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
    """Remote training via configured cloud provider (stub|modal|hf_jobs|runpod)."""

    name = "cloud"

    def start(self, db: Session, job: FinetuneJob) -> None:
        from .cloud_finetune import TrainRecipe, get_cloud_provider
        from .config import settings

        backend_name = (settings.cloud_finetune_backend or "stub").strip().lower()
        try:
            provider = get_cloud_provider(backend_name)
            provider.validate_config()
        except Exception as exc:
            update_job(db, job, status="failed", error=str(exc))
            append_log(db, job, f"Cloud provider error: {exc}")
            return

        cfg = job.get_config() or {}
        cfg["backend"] = "cloud"
        cfg["cloud_provider"] = provider.name
        job.config_json = json.dumps(cfg)
        db.commit()

        update_job(db, job, status="queued", progress=0.01)
        append_log(db, job, f"Starting cloud fine-tune via provider={provider.name}")

        t = threading.Thread(
            target=_run_cloud_job,
            args=(job.id, provider.name),
            daemon=True,
        )
        t.start()


def _dataset_dir_for(job: FinetuneJob, db: Session) -> Path:
    ensure_dirs()
    root = DATASETS_DIR / job.dataset_id
    root.mkdir(parents=True, exist_ok=True)
    # Ensure samples referenced by DB exist under the dataset folder when possible.
    samples = db.query(Sample).filter(Sample.dataset_id == job.dataset_id).all()
    manifest = []
    for s in samples:
        manifest.append(
            {
                "id": s.id,
                "split": s.split,
                "transcript": s.transcript,
                "audio_path": s.audio_path,
            }
        )
    (root / "cloud_manifest.json").write_text(json.dumps(manifest, indent=2))
    return root


def _run_cloud_job(job_id: str, provider_name: str) -> None:
    from .cloud_finetune import TrainRecipe, get_cloud_provider

    db = SessionLocal()
    try:
        job = db.get(FinetuneJob, job_id)
        if not job:
            return
        provider = get_cloud_provider(provider_name)
        cfg = job.get_config() or {}
        recipe = TrainRecipe(
            job_id=job.id,
            dataset_id=job.dataset_id,
            base_model=job.base_model,
            epochs=int(cfg.get("epochs", 3)),
            lora_rank=int(cfg.get("lora_rank", 16)),
            learning_rate=float(cfg.get("learning_rate", 1e-4)),
            batch_size=int(cfg.get("batch_size", 1)),
            language=str(cfg.get("language", "en")),
        )
        dataset_dir = _dataset_dir_for(job, db)
        update_job(db, job, status="running", progress=0.05)
        append_log(db, job, f"Submitting to {provider.name}; dataset={dataset_dir}")

        ref = provider.submit(recipe, dataset_dir)
        cfg["remote_id"] = ref.remote_id
        cfg["remote_provider"] = ref.provider
        job.config_json = json.dumps(cfg)
        db.commit()

        while True:
            job = db.get(FinetuneJob, job_id)
            if not job:
                return
            if job.cancelled:
                provider.cancel(ref)
                update_job(db, job, status="cancelled")
                append_log(db, job, "Cancelled by user")
                return

            st = provider.poll(ref)
            update_job(db, job, status=st.status if st.status != "queued" else "running", progress=st.progress)
            if st.logs_tail:
                append_log(db, job, st.logs_tail)

            if st.status == "completed":
                dest = ADAPTERS_DIR / job_id
                provider.download_adapter(ref, dest)
                update_job(
                    db,
                    job,
                    status="completed",
                    progress=1.0,
                    adapter_path=str(dest),
                )
                append_log(db, job, f"Adapter saved to {dest}")
                return
            if st.status in {"failed", "cancelled"}:
                update_job(
                    db,
                    job,
                    status=st.status,
                    error=st.error or f"Remote job {st.status}",
                )
                return
            time.sleep(0.5)
    except Exception as exc:
        job = db.get(FinetuneJob, job_id)
        if job:
            update_job(db, job, status="failed", error=str(exc))
            append_log(db, job, f"Cloud job error: {exc}")
    finally:
        db.close()


def get_backend(name: BackendName = "local") -> FinetuneBackend:
    if name == "local":
        return LocalFinetuneBackend()
    if name == "cloud":
        return CloudFinetuneBackend()
    raise ValueError(f"Unknown fine-tune backend: {name}")
