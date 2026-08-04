import pytest

from stt_lab.policy import DataPolicy, validate_mode
from stt_lab.profiles import RunnableProfile, STTConfig


def test_fully_local_rejects_cloud_flags():
    policy = DataPolicy(allow_cloud_audio=True)
    with pytest.raises(ValueError):
        validate_mode("fully_local", policy, "local")


def test_cloud_stt_requires_audio_flag():
    policy = DataPolicy(allow_cloud_audio=False)
    with pytest.raises(ValueError):
        validate_mode("cloud_stt", policy, "cloud")


def test_profile_local_ok():
    p = RunnableProfile(
        id="t1",
        name="test",
        mode="fully_local",
        stt=STTConfig(provider="whisper-tiny", location="local"),
        policy=DataPolicy(),
    )
    p.validate_consistency()
