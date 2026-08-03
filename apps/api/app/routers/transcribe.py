from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TranscribeResponse
from ..services.audio import save_upload
from ..services.transcribe import run_transcription

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])


@router.post("", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    model_ids: str = Form(...),
    reference: str | None = Form(None),
    language: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        ids = json.loads(model_ids) if model_ids.strip().startswith("[") else [
            m.strip() for m in model_ids.split(",") if m.strip()
        ]
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Invalid model_ids: {exc}") from exc
    if not ids:
        raise HTTPException(400, "Select at least one model")

    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty audio upload")
    path = await save_upload(audio.filename, data)
    try:
        return await run_transcription(
            db,
            path,
            ids,
            reference=reference or None,
            language=language or None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
