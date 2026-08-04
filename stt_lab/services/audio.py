from __future__ import annotations

from pathlib import Path


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
