from __future__ import annotations

import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import RUNS_DIR, ensure_dirs
from ..db import FinetuneJob, Sample, SessionLocal, utcnow
from ..providers.registry import adapter_dir_for

_jobs_lock = threading.Lock()
_running: dict[str, threading.Thread] = {}


def append_log(db: Session, job: FinetuneJob, line: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    job.logs = (job.logs or "") + f"[{stamp}] {line}\n"
    job.updated_at = utcnow()
    db.commit()


def update_job(
    db: Session,
    job: FinetuneJob,
    *,
    status: str | None = None,
    progress: float | None = None,
    error: str | None = None,
    adapter_path: str | None = None,
) -> None:
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if error is not None:
        job.error = error
    if adapter_path is not None:
        job.adapter_path = adapter_path
    job.updated_at = utcnow()
    db.commit()


def _is_cancelled(job_id: str) -> bool:
    db = SessionLocal()
    try:
        job = db.get(FinetuneJob, job_id)
        return bool(job and job.cancelled)
    finally:
        db.close()


def _run_finetune(job_id: str) -> None:
    ensure_dirs()
    db = SessionLocal()
    try:
        job = db.get(FinetuneJob, job_id)
        if not job:
            return
        update_job(db, job, status="running", progress=0.02)
        append_log(db, job, f"Starting LoRA fine-tune on whisper-{job.base_model}")

        samples = (
            db.query(Sample)
            .filter(Sample.dataset_id == job.dataset_id, Sample.split == "train")
            .all()
        )
        if len(samples) < 1:
            update_job(db, job, status="failed", error="No train samples in dataset")
            append_log(db, job, "Failed: no train samples")
            return

        cfg = job.get_config()
        language = cfg.get("language", "en")
        epochs = int(cfg.get("epochs", 3))
        lr = float(cfg.get("learning_rate", 1e-4))
        lora_rank = int(cfg.get("lora_rank", 16))
        lora_alpha = int(cfg.get("lora_alpha", 32))
        batch_size = int(cfg.get("batch_size", 1))

        append_log(db, job, f"Train samples: {len(samples)}")
        append_log(
            db,
            job,
            f"Config: rank={lora_rank} alpha={lora_alpha} lr={lr} epochs={epochs} bs={batch_size}",
        )

        if _is_cancelled(job_id):
            update_job(db, job, status="cancelled", progress=0)
            append_log(db, job, "Cancelled before training")
            return

        import torch
        from datasets import Dataset as HFDataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
            WhisperForConditionalGeneration,
            WhisperProcessor,
            TrainerCallback,
        )

        class ProgressCallback(TrainerCallback):
            def __init__(self, job_id: str):
                self.job_id = job_id

            def on_log(self, args, state, control, logs=None, **kwargs):  # type: ignore[no-untyped-def]
                if _is_cancelled(self.job_id):
                    control.should_training_stop = True
                    return
                local = SessionLocal()
                try:
                    j = local.get(FinetuneJob, self.job_id)
                    if not j:
                        return
                    if state.max_steps and state.max_steps > 0:
                        j.progress = min(0.95, 0.1 + 0.85 * (state.global_step / state.max_steps))
                    if logs:
                        append_log(local, j, f"step={state.global_step} {logs}")
                    else:
                        local.commit()
                finally:
                    local.close()

        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        append_log(db, job, f"Device: {device}")
        if device == "cpu":
            append_log(db, job, "WARNING: training on CPU — expect very slow runs")

        hf_id = f"openai/whisper-{job.base_model}"
        update_job(db, job, progress=0.08)
        append_log(db, job, f"Loading processor/model {hf_id}")

        processor = WhisperProcessor.from_pretrained(hf_id, language=language, task="transcribe")
        model = WhisperForConditionalGeneration.from_pretrained(hf_id)
        model.config.forced_decoder_ids = None
        model.config.suppress_tokens = []

        lora_config = LoraConfig(
            r=lora_rank,
            lora_alpha=lora_alpha,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        )
        model = get_peft_model(model, lora_config)
        update_job(db, job, progress=0.12)

        rows = []
        for s in samples:
            if not Path(s.audio_path).exists() or not s.transcript.strip():
                continue
            rows.append({"audio_path": s.audio_path, "text": s.transcript.strip()})
        if not rows:
            update_job(db, job, status="failed", error="No valid train samples with audio+text")
            append_log(db, job, "Failed: no valid samples")
            return

        # Map one-by-one for simplicity / lower memory
        processed = []
        for i, row in enumerate(rows):
            if _is_cancelled(job_id):
                update_job(db, job, status="cancelled")
                append_log(db, job, "Cancelled during preprocessing")
                return
            import librosa

            arr, _ = librosa.load(row["audio_path"], sr=16000, mono=True)
            feats = processor.feature_extractor(arr, sampling_rate=16000, return_tensors="pt")
            labels = processor.tokenizer(row["text"], return_tensors="pt").input_ids[0]
            processed.append(
                {
                    "input_features": feats.input_features[0].numpy(),
                    "labels": labels.numpy(),
                }
            )
            update_job(db, job, progress=0.12 + 0.2 * ((i + 1) / len(rows)))
        train_ds = HFDataset.from_list(
            [
                {
                    "input_features": p["input_features"],
                    "labels": p["labels"],
                }
                for p in processed
            ]
        )

        class DataCollatorSpeechSeq2SeqWithPadding:
            def __init__(self, processor):
                self.processor = processor

            def __call__(self, features):
                import torch

                input_features = [
                    {"input_features": f["input_features"]} for f in features
                ]
                batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
                label_features = [{"input_ids": f["labels"]} for f in features]
                labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
                labels = labels_batch["input_ids"].masked_fill(
                    labels_batch.attention_mask.ne(1), -100
                )
                batch["labels"] = labels
                return batch

        out_dir = RUNS_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        adapter_path = adapter_dir_for(job_id)

        use_fp16 = device == "cuda"
        args = Seq2SeqTrainingArguments(
            output_dir=str(out_dir),
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=lr,
            num_train_epochs=epochs,
            fp16=use_fp16,
            logging_steps=1,
            save_strategy="no",
            report_to=[],
            remove_unused_columns=False,
            predict_with_generate=False,
            dataloader_num_workers=0,
        )

        # Move model to device for MPS/CPU manually if needed
        if device == "mps":
            model.to("mps")

        trainer = Seq2SeqTrainer(
            args=args,
            model=model,
            train_dataset=train_ds,
            data_collator=DataCollatorSpeechSeq2SeqWithPadding(processor),
            processing_class=processor.feature_extractor,
            callbacks=[ProgressCallback(job_id)],
        )

        append_log(db, job, "Training started")
        update_job(db, job, progress=0.35)
        trainer.train()

        if _is_cancelled(job_id):
            update_job(db, job, status="cancelled")
            append_log(db, job, "Cancelled after training loop")
            return

        model.save_pretrained(str(adapter_path))
        processor.save_pretrained(str(adapter_path))
        append_log(db, job, f"Adapter saved to {adapter_path}")
        update_job(
            db,
            job,
            status="completed",
            progress=1.0,
            adapter_path=str(adapter_path),
        )
        append_log(db, job, "Fine-tune completed")
    except Exception as exc:
        tb = traceback.format_exc()
        job = db.get(FinetuneJob, job_id)
        if job:
            update_job(db, job, status="failed", error=str(exc))
            append_log(db, job, f"ERROR: {exc}\n{tb}")
    finally:
        db.close()
        with _jobs_lock:
            _running.pop(job_id, None)


def start_finetune_job(db: Session, job: FinetuneJob) -> None:
    with _jobs_lock:
        if job.id in _running:
            return
        t = threading.Thread(target=_run_finetune, args=(job.id,), daemon=True)
        _running[job.id] = t
        t.start()


def cancel_finetune_job(db: Session, job: FinetuneJob) -> FinetuneJob:
    job.cancelled = 1
    if job.status in ("queued", "running"):
        job.status = "cancelled"
    job.updated_at = utcnow()
    db.commit()
    db.refresh(job)
    return job
