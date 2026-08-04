import json
import time
import uuid
from pathlib import Path

from stt_lab.config import ADAPTERS_DIR, DATASETS_DIR, ensure_dirs
from stt_lab.db import Dataset, FinetuneJob, Sample, SessionLocal, init_db, utcnow
from stt_lab.finetune_backends import get_backend
from stt_lab.services.finetune import job_snapshot


def test_stub_cloud_finetune_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_FINETUNE_BACKEND", "stub")
    # Reload settings picks env via pydantic - use monkeypatch on settings object
    from stt_lab import config

    monkeypatch.setattr(config.settings, "cloud_finetune_backend", "stub")

    ensure_dirs()
    init_db()
    ds_id = uuid.uuid4().hex
    job_id = uuid.uuid4().hex
    ds_dir = DATASETS_DIR / ds_id
    ds_dir.mkdir(parents=True, exist_ok=True)
    (ds_dir / "a.wav").write_bytes(b"RIFF")

    db = SessionLocal()
    try:
        db.add(Dataset(id=ds_id, name="stub-ds", description=""))
        db.add(
            Sample(
                id=uuid.uuid4().hex,
                dataset_id=ds_id,
                audio_path=str(ds_dir / "a.wav"),
                transcript="hello",
                split="train",
            )
        )
        db.add(
            Sample(
                id=uuid.uuid4().hex,
                dataset_id=ds_id,
                audio_path=str(ds_dir / "a.wav"),
                transcript="hello",
                split="val",
            )
        )
        job = FinetuneJob(
            id=job_id,
            dataset_id=ds_id,
            base_model="tiny",
            status="queued",
            progress=0.0,
            logs="",
            config_json=json.dumps({"backend": "cloud", "epochs": 1}),
        )
        db.add(job)
        db.commit()
        get_backend("cloud").start(db, job)
    finally:
        db.close()

    deadline = time.time() + 15
    final = None
    while time.time() < deadline:
        db = SessionLocal()
        try:
            job = db.get(FinetuneJob, job_id)
            assert job is not None
            final = job_snapshot(job)
        finally:
            db.close()
        if final["status"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.2)

    assert final is not None
    assert final["status"] == "completed", final
    assert (ADAPTERS_DIR / job_id / "STUB_ADAPTER.json").exists()
