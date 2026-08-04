"""Data residency policy — evaluated before any network I/O."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Mode = Literal["fully_local", "hybrid_local_stt", "cloud_stt"]


class DataPolicy(BaseModel):
    allow_cloud_audio: bool = False
    allow_cloud_transcript: bool = False
    store_audio_locally: bool = True
    store_transcript_locally: bool = True
    # "forever" | "none" | "days:N"
    retention: str = "days:30"

    def allows_cloud_stt(self) -> bool:
        return self.allow_cloud_audio

    def allows_cloud_polish(self) -> bool:
        return self.allow_cloud_transcript


class PrivacyTrace(BaseModel):
    """What left the device during a single dictate run."""

    mode: Mode
    audio_left_device: bool = False
    transcript_left_device: bool = False
    stt_location: Literal["local", "cloud"]
    polish_location: Literal["off", "local", "cloud"] = "off"
    endpoint: str | None = None


def validate_mode(mode: Mode, policy: DataPolicy, stt_location: Literal["local", "cloud"]) -> None:
    if mode == "fully_local":
        if policy.allow_cloud_audio or policy.allow_cloud_transcript:
            raise ValueError("fully_local mode forbids cloud audio/transcript flags")
        if stt_location != "local":
            raise ValueError("fully_local mode requires local STT")
    if mode == "cloud_stt" and not policy.allow_cloud_audio:
        raise ValueError("cloud_stt requires allow_cloud_audio=true")
    if stt_location == "cloud" and not policy.allow_cloud_audio:
        raise ValueError("Cloud STT blocked by policy.allow_cloud_audio=false")


def mode_from_policy(
    policy: DataPolicy, stt_location: Literal["local", "cloud"]
) -> Mode:
    if stt_location == "cloud":
        return "cloud_stt"
    if policy.allow_cloud_transcript:
        return "hybrid_local_stt"
    return "fully_local"
