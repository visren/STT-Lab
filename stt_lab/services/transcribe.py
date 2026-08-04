from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import TranscribeResponse, TranscriptResult
from ..providers.registry import get_providers_by_ids
from .audio import probe_duration
from .metrics import compute_wer_cer, word_diff


async def run_transcription(
    db: Session,
    audio_path: Path,
    model_ids: list[str],
    reference: str | None = None,
    language: str | None = None,
) -> TranscribeResponse:
    providers = get_providers_by_ids(db, model_ids)
    duration = probe_duration(audio_path)

    async def _one(provider) -> TranscriptResult:
        ready, reason = provider.ready()
        if not ready:
            return TranscriptResult(
                model_id=provider.id,
                model_name=provider.name,
                provider=provider.provider,
                transcript="",
                latency_ms=0,
                audio_duration_sec=duration,
                error=reason or "Provider not ready",
            )
        result = await provider.transcribe(str(audio_path), language=language)
        wer_v, cer_v = compute_wer_cer(reference, result.transcript)
        rtf = None
        if duration and duration > 0 and result.latency_ms is not None:
            rtf = (result.latency_ms / 1000.0) / duration
        return TranscriptResult(
            model_id=provider.id,
            model_name=provider.name,
            provider=provider.provider,
            transcript=result.transcript,
            latency_ms=result.latency_ms,
            audio_duration_sec=duration,
            rtf=rtf,
            wer=wer_v,
            cer=cer_v,
            error=result.error,
            words=result.transcript.split(),
            diff_ops=word_diff(reference, result.transcript) if not result.error else [],
        )

    results = await asyncio.gather(*[_one(p) for p in providers])
    return TranscribeResponse(
        run_id=uuid.uuid4().hex,
        audio_path=str(audio_path),
        audio_duration_sec=duration,
        reference=reference,
        results=list(results),
    )
