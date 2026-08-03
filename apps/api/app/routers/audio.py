from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import DATA_DIR

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("")
def get_audio(path: str):
    target = Path(path).resolve()
    data_root = DATA_DIR.resolve()
    if not str(target).startswith(str(data_root)):
        raise HTTPException(400, "Path outside data directory")
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "Audio not found")
    return FileResponse(target)
