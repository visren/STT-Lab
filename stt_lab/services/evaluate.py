from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..db import EvaluationRun, Sample, utcnow
from ..models import EvaluateResponse, EvaluateSampleResult
from ..providers.local_whisper import AdaptedWhisperProvider, FasterWhisperProvider
from .metrics import compute_wer_cer


def run_evaluation(
    db: Session,
    *,
    dataset_id: str,
    base_model: str,
    adapter_id: str | None,
    split: str = "val",
) -> EvaluateResponse:
    samples = (
        db.query(Sample)
        .filter(Sample.dataset_id == dataset_id, Sample.split == split)
        .all()
    )
    if not samples:
        raise ValueError(f"No samples in split '{split}' for dataset")

    base = FasterWhisperProvider(base_model)
    adapted = None
    if adapter_id:
        from ..db import FinetuneJob

        job = db.get(FinetuneJob, adapter_id)
        if not job or not job.adapter_path or not Path(job.adapter_path).exists():
            raise ValueError("Adapter not found or incomplete")
        adapted = AdaptedWhisperProvider(
            adapter_id=job.id,
            base_model=job.base_model,
            adapter_path=job.adapter_path,
        )

    sample_results: list[EvaluateSampleResult] = []
    base_wers: list[float] = []
    adapted_wers: list[float] = []
    base_cers: list[float] = []
    adapted_cers: list[float] = []

    for s in samples:
        if not Path(s.audio_path).exists():
            continue
        base_res = base._transcribe_sync(s.audio_path, None)
        b_wer, b_cer = compute_wer_cer(s.transcript, base_res.transcript)
        a_text = None
        a_wer = a_cer = None
        if adapted:
            a_res = adapted._transcribe_sync(s.audio_path, None)
            a_text = a_res.transcript
            a_wer, a_cer = compute_wer_cer(s.transcript, a_res.transcript)
            if a_wer is not None:
                adapted_wers.append(a_wer)
            if a_cer is not None:
                adapted_cers.append(a_cer)
        if b_wer is not None:
            base_wers.append(b_wer)
        if b_cer is not None:
            base_cers.append(b_cer)
        sample_results.append(
            EvaluateSampleResult(
                sample_id=s.id,
                reference=s.transcript,
                base_transcript=base_res.transcript,
                adapted_transcript=a_text,
                base_wer=b_wer,
                adapted_wer=a_wer,
                base_cer=b_cer,
                adapted_cer=a_cer,
            )
        )

    def avg(xs: list[float]) -> float | None:
        return sum(xs) / len(xs) if xs else None

    base_wer = avg(base_wers)
    adapted_wer = avg(adapted_wers)
    base_cer = avg(base_cers)
    adapted_cer = avg(adapted_cers)
    delta_wer = (
        (adapted_wer - base_wer) if base_wer is not None and adapted_wer is not None else None
    )
    delta_cer = (
        (adapted_cer - base_cer) if base_cer is not None and adapted_cer is not None else None
    )

    run_id = uuid.uuid4().hex
    payload = EvaluateResponse(
        id=run_id,
        dataset_id=dataset_id,
        base_model=base_model,
        adapter_id=adapter_id,
        split=split,
        sample_count=len(sample_results),
        base_wer=base_wer,
        adapted_wer=adapted_wer,
        delta_wer=delta_wer,
        base_cer=base_cer,
        adapted_cer=adapted_cer,
        delta_cer=delta_cer,
        samples=sample_results,
    )
    row = EvaluationRun(
        id=run_id,
        dataset_id=dataset_id,
        base_model=base_model,
        adapter_id=adapter_id,
        split=split,
        results_json=payload.model_dump_json(),
        created_at=utcnow(),
    )
    db.add(row)
    db.commit()
    return payload
