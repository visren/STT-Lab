"""CLI for the model build/test environment."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from stt_lab.config import ensure_dirs
from stt_lab.db import SessionLocal, init_db
from stt_lab.providers.registry import list_models
from stt_lab.services.finetune import enqueue_finetune, wait_for_finetune
from stt_lab.services.transcribe import run_transcription


def cmd_smoke(args: argparse.Namespace) -> None:
    ensure_dirs()
    init_db()
    audio = Path(args.audio).expanduser().resolve()
    if not audio.exists():
        raise SystemExit(f"Audio not found: {audio}")
    model_ids = [m.strip() for m in args.models.split(",") if m.strip()]
    db = SessionLocal()
    try:
        resp = asyncio.run(
            run_transcription(db, audio, model_ids, reference=args.reference or None)
        )
    finally:
        db.close()
    print(json.dumps(resp.model_dump(), indent=2))


def cmd_models(_: argparse.Namespace) -> None:
    init_db()
    db = SessionLocal()
    try:
        for m in list_models(db):
            flag = "ready" if m.ready else f"blocked:{m.reason}"
            print(f"{m.id:40} {m.provider:12} {flag}")
    finally:
        db.close()


def cmd_finetune(args: argparse.Namespace) -> None:
    ensure_dirs()
    init_db()
    db = SessionLocal()
    try:
        job = enqueue_finetune(
            db,
            dataset_id=args.dataset_id,
            base_model=args.base_model,
            epochs=args.epochs,
            lora_rank=args.lora_rank,
            backend=args.backend,
        )
        job_id = job.id
    finally:
        db.close()
    print("job_id:", job_id)
    if args.wait:
        def _print(st: dict) -> None:
            print(f"{st['status']}  progress={st['progress']:.0%}")

        st = wait_for_finetune(job_id, on_poll=_print)
        if st.get("logs_tail"):
            print(st["logs_tail"])
        if st.get("error"):
            print("ERROR:", st["error"])
        print(json.dumps(st, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="STT model-lab commands")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_models = sub.add_parser("models", help="List runnable providers")
    p_models.set_defaults(func=cmd_models)

    p_smoke = sub.add_parser("smoke", help="Transcribe a clip with one or more models")
    p_smoke.add_argument("--audio", required=True)
    p_smoke.add_argument("--models", default="whisper-tiny")
    p_smoke.add_argument("--reference", default="")
    p_smoke.set_defaults(func=cmd_smoke)

    p_ft = sub.add_parser("finetune", help="Start a LoRA fine-tune job")
    p_ft.add_argument("--dataset-id", required=True)
    p_ft.add_argument("--base-model", default="tiny")
    p_ft.add_argument("--epochs", type=int, default=1)
    p_ft.add_argument("--lora-rank", type=int, default=8)
    p_ft.add_argument("--backend", default="local", choices=["local", "cloud"])
    p_ft.add_argument("--wait", action="store_true")
    p_ft.set_defaults(func=cmd_finetune)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
