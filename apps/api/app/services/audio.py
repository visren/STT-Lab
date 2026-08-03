from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles

from ..config import AUDIO_DIR, ensure_dirs


async def save_upload(filename: str | None, data: bytes) -> Path:
    ensure_dirs()
    suffix = Path(filename or "audio.wav").suffix or ".wav"
    path = AUDIO_DIR / f"{uuid.uuid4().hex}{suffix}"
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)
    return path


def probe_duration(audio_path: str | Path) -> float | None:
    path = Path(audio_path)
    try:
        import soundfile as sf

        info = sf.info(str(path))
        return float(info.duration)
    except Exception:
        pass
    try:
        import librosa

        return float(librosa.get_duration(path=str(path)))
    except Exception:
        return None
