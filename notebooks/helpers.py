"""Helpers for the STT Lab Jupyter notebook.

Uses the FastAPI app modules directly (no HTTP server required).
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.config import DATASETS_DIR, ensure_dirs  # noqa: E402
from app.db import Dataset, FinetuneJob, Sample, SessionLocal, init_db, utcnow  # noqa: E402
from app.providers.registry import list_models  # noqa: E402
from app.services.audio import probe_duration  # noqa: E402
from app.services.evaluate import run_evaluation  # noqa: E402
from app.services.finetune import start_finetune_job  # noqa: E402
from app.services.metrics import word_diff  # noqa: E402
from app.services.transcribe import run_transcription  # noqa: E402

ensure_dirs()
init_db()


def models_df() -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = [m.model_dump() for m in list_models(db)]
    finally:
        db.close()
    return pd.DataFrame(rows)


async def compare_async(
    audio_path: str | Path,
    model_ids: list[str],
    reference: str | None = None,
    language: str | None = None,
):
    path = Path(audio_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    db = SessionLocal()
    try:
        return await run_transcription(
            db,
            path,
            model_ids,
            reference=reference or None,
            language=language or None,
        )
    finally:
        db.close()


def compare(
    audio_path: str | Path,
    model_ids: list[str],
    reference: str | None = None,
    language: str | None = None,
):
    return asyncio.run(compare_async(audio_path, model_ids, reference, language))


def results_df(response) -> pd.DataFrame:
    rows = []
    for r in response.results:
        rows.append(
            {
                "model": r.model_name,
                "model_id": r.model_id,
                "provider": r.provider,
                "latency_ms": round(r.latency_ms, 1),
                "rtf": None if r.rtf is None else round(r.rtf, 3),
                "wer": None if r.wer is None else round(r.wer, 4),
                "cer": None if r.cer is None else round(r.cer, 4),
                "error": r.error,
                "transcript": r.transcript,
            }
        )
    return pd.DataFrame(rows)


def show_diff(reference: str | None, hypothesis: str) -> str:
    ops = word_diff(reference, hypothesis)
    parts = []
    for op in ops:
        if op["op"] == "equal":
            parts.append(op["text"])
        elif op["op"] == "insert":
            parts.append(f"[+{op['text']}]")
        elif op["op"] == "delete":
            parts.append(f"[-{op['text']}]")
        else:
            parts.append(f"[{op['text']}]")
    return " ".join(parts)


def create_dataset(name: str, description: str = "") -> str:
    db = SessionLocal()
    try:
        d = Dataset(
            id=uuid.uuid4().hex,
            name=name.strip() or "Notebook dataset",
            description=description,
        )
        db.add(d)
        db.commit()
        (DATASETS_DIR / d.id).mkdir(parents=True, exist_ok=True)
        return d.id
    finally:
        db.close()


def add_sample(
    dataset_id: str,
    audio_path: str | Path,
    transcript: str,
    split: str = "train",
) -> str:
    if split not in ("train", "val"):
        raise ValueError("split must be train or val")
    src = Path(audio_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    dest_dir = DATASETS_DIR / dataset_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if src != dest:
        shutil.copy2(src, dest)

    db = SessionLocal()
    try:
        ds = db.get(Dataset, dataset_id)
        if not ds:
            raise ValueError(f"Unknown dataset: {dataset_id}")
        s = Sample(
            id=uuid.uuid4().hex,
            dataset_id=dataset_id,
            audio_path=str(dest),
            transcript=transcript,
            split=split,
            duration_sec=probe_duration(dest),
        )
        ds.updated_at = utcnow()
        db.add(s)
        db.commit()
        return s.id
    finally:
        db.close()


def list_datasets() -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = []
        for d in db.query(Dataset).order_by(Dataset.updated_at.desc()).all():
            samples = d.samples or []
            rows.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "samples": len(samples),
                    "train": sum(1 for s in samples if s.split == "train"),
                    "val": sum(1 for s in samples if s.split == "val"),
                    "updated_at": d.updated_at.isoformat(),
                }
            )
        return pd.DataFrame(rows)
    finally:
        db.close()


def start_finetune(
    dataset_id: str,
    base_model: str = "tiny",
    epochs: int = 3,
    lora_rank: int = 16,
    learning_rate: float = 1e-4,
    batch_size: int = 1,
    language: str = "en",
) -> str:
    import json

    db = SessionLocal()
    try:
        train_count = (
            db.query(Sample)
            .filter(Sample.dataset_id == dataset_id, Sample.split == "train")
            .count()
        )
        val_count = (
            db.query(Sample)
            .filter(Sample.dataset_id == dataset_id, Sample.split == "val")
            .count()
        )
        if train_count < 1:
            raise ValueError("Need at least 1 train sample")
        if val_count < 1:
            raise ValueError("Need at least 1 val sample")

        cfg = {
            "lora_rank": lora_rank,
            "lora_alpha": 32,
            "learning_rate": learning_rate,
            "epochs": epochs,
            "batch_size": batch_size,
            "language": language,
            "train_count": train_count,
            "val_count": val_count,
            "warn_low_samples": train_count < 30,
        }
        job = FinetuneJob(
            id=uuid.uuid4().hex,
            dataset_id=dataset_id,
            base_model=base_model,
            status="queued",
            progress=0.0,
            logs="",
            config_json=json.dumps(cfg),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        start_finetune_job(db, job)
        return job.id
    finally:
        db.close()


def job_status(job_id: str) -> dict:
    db = SessionLocal()
    try:
        job = db.get(FinetuneJob, job_id)
        if not job:
            raise ValueError(f"Unknown job: {job_id}")
        return {
            "id": job.id,
            "status": job.status,
            "progress": job.progress,
            "error": job.error,
            "adapter_path": job.adapter_path,
            "logs_tail": "\n".join((job.logs or "").splitlines()[-20:]),
        }
    finally:
        db.close()


def wait_for_job(job_id: str, poll_sec: float = 2.0, timeout_sec: float = 3600):
    import time

    started = time.time()
    while True:
        st = job_status(job_id)
        print(f"{st['status']}  progress={st['progress']:.0%}")
        if st["status"] in ("completed", "failed", "cancelled"):
            if st["logs_tail"]:
                print(st["logs_tail"])
            if st["error"]:
                print("ERROR:", st["error"])
            return st
        if time.time() - started > timeout_sec:
            raise TimeoutError(f"Job {job_id} still {st['status']} after {timeout_sec}s")
        time.sleep(poll_sec)


def evaluate(dataset_id: str, base_model: str, adapter_id: str | None, split: str = "val"):
    db = SessionLocal()
    try:
        return run_evaluation(
            db,
            dataset_id=dataset_id,
            base_model=base_model,
            adapter_id=adapter_id,
            split=split,
        )
    finally:
        db.close()


def eval_df(response) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reference": s.reference,
                "base": s.base_transcript,
                "adapted": s.adapted_transcript,
                "base_wer": s.base_wer,
                "adapted_wer": s.adapted_wer,
            }
            for s in response.samples
        ]
    )


def load_catalog() -> dict:
    import json

    path = Path(__file__).resolve().parent / "models_catalog.json"
    return json.loads(path.read_text())


def catalog_df(
    *,
    status: str | None = None,
    role: str | None = None,
    mode: str | None = None,
    family: str | None = None,
) -> pd.DataFrame:
    rows = load_catalog()["models"]
    df = pd.DataFrame(rows)
    if status:
        df = df[df["status"] == status]
    if mode:
        df = df[df["mode"] == mode]
    if family:
        df = df[df["family"] == family]
    if role:
        df = df[df["roles"].apply(lambda rs: role in (rs or []))]
    return df.reset_index(drop=True)
