from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import Dataset, FinetuneJob, Sample, get_db, utcnow
from ..models import FinetuneJobOut, FinetuneRequest
from ..services.finetune import cancel_finetune_job, start_finetune_job

router = APIRouter(prefix="/api/finetune", tags=["finetune"])


def _job_out(job: FinetuneJob) -> FinetuneJobOut:
    return FinetuneJobOut(
        id=job.id,
        dataset_id=job.dataset_id,
        base_model=job.base_model,
        status=job.status,
        progress=job.progress,
        logs=job.logs or "",
        adapter_path=job.adapter_path,
        error=job.error,
        config=job.get_config(),
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        cancelled=bool(job.cancelled),
    )


@router.get("", response_model=list[FinetuneJobOut])
def list_jobs(db: Session = Depends(get_db)):
    rows = db.query(FinetuneJob).order_by(FinetuneJob.created_at.desc()).all()
    return [_job_out(j) for j in rows]


@router.post("", response_model=FinetuneJobOut)
def create_job(body: FinetuneRequest, db: Session = Depends(get_db)):
    ds = db.get(Dataset, body.dataset_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    train_count = (
        db.query(Sample)
        .filter(Sample.dataset_id == body.dataset_id, Sample.split == "train")
        .count()
    )
    val_count = (
        db.query(Sample)
        .filter(Sample.dataset_id == body.dataset_id, Sample.split == "val")
        .count()
    )
    if train_count < 1:
        raise HTTPException(400, "Dataset needs at least 1 train sample")
    if val_count < 1:
        raise HTTPException(400, "Dataset needs at least 1 val sample for evaluation")

    cfg = {
        "lora_rank": body.lora_rank,
        "lora_alpha": body.lora_alpha,
        "learning_rate": body.learning_rate,
        "epochs": body.epochs,
        "batch_size": body.batch_size,
        "language": body.language,
        "train_count": train_count,
        "val_count": val_count,
        "warn_low_samples": train_count < 30,
    }
    job = FinetuneJob(
        id=uuid.uuid4().hex,
        dataset_id=body.dataset_id,
        base_model=body.base_model,
        status="queued",
        progress=0.0,
        logs="",
        config_json=json.dumps(cfg),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    start_finetune_job(db, job)
    return _job_out(job)


@router.get("/{job_id}", response_model=FinetuneJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(FinetuneJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _job_out(job)


@router.post("/{job_id}/cancel", response_model=FinetuneJobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(FinetuneJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job = cancel_finetune_job(db, job)
    return _job_out(job)
