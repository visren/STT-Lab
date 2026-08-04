"""STT Lab HTTP API — compare, datasets, fine-tune, evaluate."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stt_lab.config import (  # noqa: E402
    AUDIO_DIR,
    DATASETS_DIR,
    DATA_DIR,
    ensure_dirs,
    settings,
)
from stt_lab.db import (  # noqa: E402
    Dataset,
    FinetuneJob,
    Sample,
    get_db,
    init_db,
    utcnow,
)
from stt_lab.finetune_backends import get_backend  # noqa: E402
from stt_lab.providers.registry import list_models  # noqa: E402
from stt_lab.services.audio import probe_duration  # noqa: E402
from stt_lab.services.evaluate import run_evaluation  # noqa: E402
from stt_lab.services.finetune import cancel_finetune_job  # noqa: E402
from stt_lab.services.transcribe import run_transcription  # noqa: E402

LOCAL_KEYS_PATH = DATA_DIR / "local_keys.json"

app = FastAPI(title="STT Lab", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    ensure_dirs()
    init_db()
    _apply_local_keys()


def _apply_local_keys() -> None:
    """Overlay keys from data/local_keys.json onto runtime settings."""
    if not LOCAL_KEYS_PATH.exists():
        return
    try:
        payload = json.loads(LOCAL_KEYS_PATH.read_text())
    except Exception:
        return
    for key, attr in (
        ("openai_api_key", "openai_api_key"),
        ("deepgram_api_key", "deepgram_api_key"),
        ("assemblyai_api_key", "assemblyai_api_key"),
        ("whisper_device", "whisper_device"),
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            setattr(settings, attr, val.strip())


def _save_upload(upload: UploadFile, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
    dest = dest_dir / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return dest


# --- Models / health ---


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "stt-lab"}


@app.get("/api/models")
def models(db: Session = Depends(get_db)) -> list[dict]:
    return [m.model_dump() for m in list_models(db)]


# --- Settings ---


class SettingsUpdate(BaseModel):
    openai_api_key: str | None = None
    deepgram_api_key: str | None = None
    assemblyai_api_key: str | None = None
    whisper_device: str | None = None


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)) -> dict:
    models_ = list_models(db)
    return {
        "whisper_device": settings.whisper_device,
        "keys": {
            "openai": bool(settings.openai_api_key),
            "deepgram": bool(settings.deepgram_api_key),
            "assemblyai": bool(settings.assemblyai_api_key),
        },
        "models": [m.model_dump() for m in models_],
    }


@app.put("/api/settings")
def update_settings(body: SettingsUpdate) -> dict:
    ensure_dirs()
    current: dict = {}
    if LOCAL_KEYS_PATH.exists():
        try:
            current = json.loads(LOCAL_KEYS_PATH.read_text())
        except Exception:
            current = {}
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        if isinstance(v, str):
            current[k] = v.strip()
    LOCAL_KEYS_PATH.write_text(json.dumps(current, indent=2))
    _apply_local_keys()
    return {"ok": True, "keys": {
        "openai": bool(settings.openai_api_key),
        "deepgram": bool(settings.deepgram_api_key),
        "assemblyai": bool(settings.assemblyai_api_key),
    }}


# --- Transcribe / compare ---


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    model_ids: str = Form(...),
    reference: str = Form(""),
    language: str = Form(""),
    db: Session = Depends(get_db),
) -> dict:
    try:
        ids = json.loads(model_ids) if model_ids.strip().startswith("[") else [
            m.strip() for m in model_ids.split(",") if m.strip()
        ]
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Invalid model_ids: {exc}") from exc
    if not ids:
        raise HTTPException(400, "Select at least one model")

    path = _save_upload(audio, AUDIO_DIR)
    try:
        resp = await run_transcription(
            db,
            path,
            ids,
            reference=reference.strip() or None,
            language=language.strip() or None,
        )
        return resp.model_dump()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# --- Datasets ---


class DatasetCreate(BaseModel):
    name: str
    description: str = ""


class SampleUpdate(BaseModel):
    transcript: str | None = None
    split: str | None = None


class SampleFromAudio(BaseModel):
    audio_path: str
    transcript: str
    split: str = "train"


@app.get("/api/datasets")
def list_datasets(db: Session = Depends(get_db)) -> list[dict]:
    rows = []
    for d in db.query(Dataset).order_by(Dataset.updated_at.desc()).all():
        samples = d.samples or []
        rows.append(
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "sample_count": len(samples),
                "train_count": sum(1 for s in samples if s.split == "train"),
                "val_count": sum(1 for s in samples if s.split == "val"),
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
        )
    return rows


@app.post("/api/datasets")
def create_dataset(body: DatasetCreate, db: Session = Depends(get_db)) -> dict:
    d = Dataset(
        id=uuid.uuid4().hex,
        name=body.name.strip() or "Untitled dataset",
        description=body.description,
    )
    db.add(d)
    db.commit()
    (DATASETS_DIR / d.id).mkdir(parents=True, exist_ok=True)
    return {"id": d.id, "name": d.name, "description": d.description}


@app.get("/api/datasets/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    samples = [
        {
            "id": s.id,
            "audio_path": s.audio_path,
            "transcript": s.transcript,
            "split": s.split,
            "duration_sec": s.duration_sec,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in (d.samples or [])
    ]
    return {
        "id": d.id,
        "name": d.name,
        "description": d.description,
        "samples": samples,
        "train_count": sum(1 for s in samples if s["split"] == "train"),
        "val_count": sum(1 for s in samples if s["split"] == "val"),
    }


@app.post("/api/datasets/{dataset_id}/samples")
async def add_sample_upload(
    dataset_id: str,
    audio: UploadFile = File(...),
    transcript: str = Form(...),
    split: str = Form("train"),
    db: Session = Depends(get_db),
) -> dict:
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    if split not in ("train", "val"):
        raise HTTPException(400, "split must be train or val")
    dest_dir = DATASETS_DIR / dataset_id
    path = _save_upload(audio, dest_dir)
    s = Sample(
        id=uuid.uuid4().hex,
        dataset_id=dataset_id,
        audio_path=str(path),
        transcript=transcript,
        split=split,
        duration_sec=probe_duration(path),
    )
    d.updated_at = utcnow()
    db.add(s)
    db.commit()
    return {"id": s.id, "audio_path": s.audio_path, "split": s.split}


@app.post("/api/datasets/{dataset_id}/samples/from-path")
def add_sample_from_path(
    dataset_id: str,
    body: SampleFromAudio,
    db: Session = Depends(get_db),
) -> dict:
    """Attach an existing audio file (e.g. from a compare run) to a dataset."""
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    if body.split not in ("train", "val"):
        raise HTTPException(400, "split must be train or val")
    src = Path(body.audio_path).expanduser().resolve()
    if not src.exists():
        raise HTTPException(400, f"Audio not found: {src}")
    dest_dir = DATASETS_DIR / dataset_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if src != dest:
        shutil.copy2(src, dest)
    s = Sample(
        id=uuid.uuid4().hex,
        dataset_id=dataset_id,
        audio_path=str(dest),
        transcript=body.transcript,
        split=body.split,
        duration_sec=probe_duration(dest),
    )
    d.updated_at = utcnow()
    db.add(s)
    db.commit()
    return {"id": s.id, "audio_path": s.audio_path, "split": s.split}


@app.patch("/api/datasets/{dataset_id}/samples/{sample_id}")
def update_sample(
    dataset_id: str,
    sample_id: str,
    body: SampleUpdate,
    db: Session = Depends(get_db),
) -> dict:
    s = db.get(Sample, sample_id)
    if not s or s.dataset_id != dataset_id:
        raise HTTPException(404, "Sample not found")
    if body.transcript is not None:
        s.transcript = body.transcript
    if body.split is not None:
        if body.split not in ("train", "val"):
            raise HTTPException(400, "split must be train or val")
        s.split = body.split
    d = db.get(Dataset, dataset_id)
    if d:
        d.updated_at = utcnow()
    db.commit()
    return {"id": s.id, "transcript": s.transcript, "split": s.split}


@app.delete("/api/datasets/{dataset_id}/samples/{sample_id}")
def delete_sample(
    dataset_id: str,
    sample_id: str,
    db: Session = Depends(get_db),
) -> dict:
    s = db.get(Sample, sample_id)
    if not s or s.dataset_id != dataset_id:
        raise HTTPException(404, "Sample not found")
    db.delete(s)
    d = db.get(Dataset, dataset_id)
    if d:
        d.updated_at = utcnow()
    db.commit()
    return {"ok": True}


@app.delete("/api/datasets/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    d = db.get(Dataset, dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    db.delete(d)
    db.commit()
    return {"ok": True}


# --- Fine-tune ---


class FinetuneCreate(BaseModel):
    dataset_id: str
    base_model: str = "tiny"
    epochs: int = 3
    lora_rank: int = 16
    lora_alpha: int = 32
    learning_rate: float = 1e-4
    batch_size: int = 1
    language: str = "en"
    backend: str = "local"


@app.get("/api/finetune")
def list_finetune_jobs(db: Session = Depends(get_db)) -> list[dict]:
    jobs = db.query(FinetuneJob).order_by(FinetuneJob.created_at.desc()).limit(50).all()
    return [_job_dict(j) for j in jobs]


@app.post("/api/finetune")
def start_finetune(body: FinetuneCreate, db: Session = Depends(get_db)) -> dict:
    d = db.get(Dataset, body.dataset_id)
    if not d:
        raise HTTPException(404, "Dataset not found")
    if body.base_model not in ("tiny", "base", "small", "medium"):
        raise HTTPException(400, "base_model must be tiny|base|small|medium")

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
        raise HTTPException(400, "Need at least 1 train sample")
    if val_count < 1:
        raise HTTPException(400, "Need at least 1 val sample for evaluation")

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
        "backend": body.backend,
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
    try:
        get_backend(body.backend).start(db, job)  # type: ignore[arg-type]
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return _job_dict(job)


@app.get("/api/finetune/{job_id}")
def get_finetune(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(FinetuneJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _job_dict(job, full_logs=True)


@app.post("/api/finetune/{job_id}/cancel")
def cancel_finetune(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(FinetuneJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job = cancel_finetune_job(db, job)
    return _job_dict(job, full_logs=True)


def _job_dict(job: FinetuneJob, full_logs: bool = False) -> dict:
    cfg = job.get_config() or {}
    logs = job.logs or ""
    return {
        "id": job.id,
        "dataset_id": job.dataset_id,
        "base_model": job.base_model,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "adapter_path": job.adapter_path,
        "config": cfg,
        "warn_low_samples": bool(cfg.get("warn_low_samples")),
        "logs": logs if full_logs else "\n".join(logs.splitlines()[-40:]),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


# --- Evaluate ---


class EvaluateRequest(BaseModel):
    dataset_id: str
    base_model: str = "tiny"
    adapter_id: str | None = None
    split: str = "val"


@app.post("/api/evaluate")
def evaluate(body: EvaluateRequest, db: Session = Depends(get_db)) -> dict:
    try:
        resp = run_evaluation(
            db,
            dataset_id=body.dataset_id,
            base_model=body.base_model,
            adapter_id=body.adapter_id,
            split=body.split,
        )
        return resp.model_dump()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
