"""Runnable profiles — handoff from research lab to dictation app."""

from __future__ import annotations

import json
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
        if self.stt.location == "cloud" and not self.cloud.stt_base_url and self.stt.provider == "openai_compatible":
            # provider-specific cloud configs may omit URL (use SDK defaults)
            pass
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
