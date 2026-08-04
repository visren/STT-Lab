"""Runnable profiles — handoff from research lab to dictation app."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .config import PROFILES_DIR, ensure_dirs
from .policy import DataPolicy, Mode, validate_mode


class STTConfig(BaseModel):
    provider: str  # local whisper id, adapted-*, openai_compatible, deepgram, ...
    base_model: str | None = None
    adapter_id: str | None = None
    model: str | None = None  # cloud model name when applicable
    language: str | None = "en"
    location: Literal["local", "cloud"] = "local"


class PolishConfig(BaseModel):
    provider: Literal["off", "local_llm", "cloud_llm"] = "off"
    model: str | None = None


class CleanupConfig(BaseModel):
    filler_words: bool = True
    dictionary_path: str | None = None


class CloudConfig(BaseModel):
    stt_base_url: str | None = None
    stt_api_key_env: str | None = None
    polish_base_url: str | None = None
    polish_api_key_env: str | None = None


class RunnableProfile(BaseModel):
    id: str
    name: str
    mode: Mode = "fully_local"
    stt: STTConfig
    polish: PolishConfig = Field(default_factory=PolishConfig)
    cleanup: CleanupConfig = Field(default_factory=CleanupConfig)
    policy: DataPolicy = Field(default_factory=DataPolicy)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    meta: dict[str, Any] = Field(default_factory=dict)

    def validate_consistency(self) -> None:
        validate_mode(self.mode, self.policy, self.stt.location)
        if self.polish.provider == "cloud_llm" and not self.policy.allow_cloud_transcript:
            raise ValueError("cloud polish requires policy.allow_cloud_transcript=true")


def profiles_dir() -> Path:
    ensure_dirs()
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR


def save_profile(profile: RunnableProfile) -> Path:
    profile.validate_consistency()
    path = profiles_dir() / f"{profile.id}.json"
    path.write_text(profile.model_dump_json(indent=2))
    return path


def load_profile(profile_id: str) -> RunnableProfile:
    path = profiles_dir() / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    profile = RunnableProfile.model_validate_json(path.read_text())
    profile.validate_consistency()
    return profile


def list_profiles() -> list[RunnableProfile]:
    out: list[RunnableProfile] = []
    for path in sorted(profiles_dir().glob("*.json")):
        try:
            out.append(RunnableProfile.model_validate_json(path.read_text()))
        except Exception:
            continue
    return out


def apply_stt_mode(
    profile: RunnableProfile,
    location: Literal["local", "cloud"],
) -> RunnableProfile:
    """Runtime local/cloud toggle for the dictation app (does not rewrite disk)."""
    p = profile.model_copy(deep=True)
    local_provider = (
        p.meta.get("local_provider")
        or (f"adapted-{p.stt.adapter_id}" if p.stt.adapter_id else None)
        or (f"whisper-{p.stt.base_model}" if p.stt.base_model else None)
        or "whisper-tiny"
    )
    cloud_provider = p.meta.get("cloud_provider") or "openai-whisper-1"

    if location == "local":
        p.stt.location = "local"
        p.stt.provider = local_provider
        p.mode = "fully_local"
        p.policy.allow_cloud_audio = False
        # Keep polish-off for fully local unless already local polish
        if p.polish.provider == "cloud_llm":
            p.polish.provider = "off"
        p.policy.allow_cloud_transcript = False
    else:
        p.stt.location = "cloud"
        p.stt.provider = cloud_provider
        p.mode = "cloud_stt"
        p.policy.allow_cloud_audio = True
        p.policy.allow_cloud_transcript = True

    p.validate_consistency()
    return p
