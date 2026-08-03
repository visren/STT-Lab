from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import DATASETS_DIR
from ..db import Dataset, Sample, get_db, utcnow
from ..models import DatasetCreate, DatasetOut, DatasetUpdate, SampleOut, SampleUpdate
from ..services.audio import probe_duration, save_upload

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _sample_out(s: Sample) -> SampleOut:
    return SampleOut(
        id=s.id,
        dataset_id=s.dataset_id,
        audio_path=s.audio_path,
        transcript=s.transcript,
        split=s.split,
        duration_sec=s.duration_sec,
        created_at=s.created_at.isoformat(),
    )


def _dataset_out(d: Dataset, include_samples: bool = False) -> DatasetOut:
    samples = d.samples or []
    return DatasetOut(
        id=d.id,
        name=d.name,
        description=d.description or "",
        created_at=d.created_at.isoformat(),
        updated_at=d.updated_at.isoformat(),
        sample_count=len(samples),
        train_count=sum(1 for s in samples if s.split == "train"),
        val_count=sum(1 for s in samples if s.split == "val"),
        samples=[_sample_out(s) for s in samples] if include_samples else [],
    )


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    rows = db.query(Dataset).order_by(Dataset.updated_at.desc()).all()
    return [_dataset_out(d) for d in rows]


@router.post("", response_model=DatasetOut)
def create_dataset(body: DatasetCreate, db: Session = Depends(get_db)):
    d = Dataset(
        id=uuid.uuid4().hex,
        name=body.name.strip() or "Untitled dataset",
        description=body.description or "",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    (DATASETS_DIR / d.id).mkdir(parents=True, exist_ok=True)
    return _dataset_out(d, include_samples=True)


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    return _dataset_out(d, include_samples=True)


@router.patch("/{dataset_id}", response_model=DatasetOut)
def update_dataset(dataset_id: str, body: DatasetUpdate, db: Session = Depends(get_db)):
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    if body.name is not None:
        d.name = body.name.strip() or d.name
    if body.description is not None:
        d.description = body.description
    d.updated_at = utcnow()
    db.commit()
    db.refresh(d)
    return _dataset_out(d, include_samples=True)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    db.delete(d)
    db.commit()
    folder = DATASETS_DIR / dataset_id
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
    return {"ok": True}


@router.post("/{dataset_id}/samples", response_model=SampleOut)
async def add_sample(
    dataset_id: str,
    audio: UploadFile | None = File(None),
    audio_path: str | None = Form(None),
    transcript: str = Form(""),
    split: str = Form("train"),
    db: Session = Depends(get_db),
):
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    if split not in ("train", "val"):
        raise HTTPException(400, "split must be train or val")

    if audio is not None:
        data = await audio.read()
        if not data:
            raise HTTPException(400, "Empty audio")
        path = await save_upload(audio.filename, data)
        # also copy into dataset folder for bookkeeping
        dest = DATASETS_DIR / dataset_id / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        final_path = str(dest)
    elif audio_path:
        src = Path(audio_path)
        if not src.exists():
            raise HTTPException(400, "audio_path does not exist")
        dest = DATASETS_DIR / dataset_id / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        final_path = str(dest)
    else:
        raise HTTPException(400, "Provide audio file or audio_path")

    s = Sample(
        id=uuid.uuid4().hex,
        dataset_id=dataset_id,
        audio_path=final_path,
        transcript=transcript or "",
        split=split,
        duration_sec=probe_duration(final_path),
    )
    d.updated_at = utcnow()
    db.add(s)
    db.commit()
    db.refresh(s)
    return _sample_out(s)


@router.patch("/{dataset_id}/samples/{sample_id}", response_model=SampleOut)
def update_sample(
    dataset_id: str,
    sample_id: str,
    body: SampleUpdate,
    db: Session = Depends(get_db),
):
    s = db.get(Sample, sample_id)
    if not s or s.dataset_id != dataset_id:
        raise HTTPException(404, "Sample not found")
    if body.transcript is not None:
        s.transcript = body.transcript
    if body.split is not None:
        s.split = body.split
    ds = db.get(Dataset, dataset_id)
    if ds:
        ds.updated_at = utcnow()
    db.commit()
    db.refresh(s)
    return _sample_out(s)


@router.delete("/{dataset_id}/samples/{sample_id}")
def delete_sample(dataset_id: str, sample_id: str, db: Session = Depends(get_db)):
    s = db.get(Sample, sample_id)
    if not s or s.dataset_id != dataset_id:
        raise HTTPException(404, "Sample not found")
    path = Path(s.audio_path)
    db.delete(s)
    ds = db.get(Dataset, dataset_id)
    if ds:
        ds.updated_at = utcnow()
    db.commit()
    if path.exists() and str(DATASETS_DIR) in str(path):
        path.unlink(missing_ok=True)
    return {"ok": True}
