from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from ..config import DATA_DIR, settings
from ..models import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _mask(value: str) -> bool:
    return bool(value and value.strip())


@router.get("", response_model=SettingsOut)
def get_settings():
    return SettingsOut(
        openai_configured=_mask(settings.openai_api_key),
        deepgram_configured=_mask(settings.deepgram_api_key),
        assemblyai_configured=_mask(settings.assemblyai_api_key),
        whisper_device=settings.whisper_device,
        data_dir=str(DATA_DIR),
    )


def _write_env(updates: dict[str, str]) -> None:
    existing: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if not line.strip() or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            existing[k.strip()] = v.strip()
    existing.update(updates)
    lines = [f"{k}={v}" for k, v in existing.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n")


@router.patch("", response_model=SettingsOut)
def update_settings(body: SettingsUpdate):
    updates: dict[str, str] = {}
    if body.openai_api_key is not None:
        settings.openai_api_key = body.openai_api_key
        updates["OPENAI_API_KEY"] = body.openai_api_key
    if body.deepgram_api_key is not None:
        settings.deepgram_api_key = body.deepgram_api_key
        updates["DEEPGRAM_API_KEY"] = body.deepgram_api_key
    if body.assemblyai_api_key is not None:
        settings.assemblyai_api_key = body.assemblyai_api_key
        updates["ASSEMBLYAI_API_KEY"] = body.assemblyai_api_key
    if body.whisper_device is not None:
        settings.whisper_device = body.whisper_device
        updates["WHISPER_DEVICE"] = body.whisper_device
    if updates:
        _write_env(updates)
    return get_settings()
