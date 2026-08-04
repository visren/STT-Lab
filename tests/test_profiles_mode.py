from stt_lab.policy import DataPolicy
from stt_lab.profiles import RunnableProfile, STTConfig, apply_stt_mode


def _base() -> RunnableProfile:
    return RunnableProfile(
        id="t",
        name="t",
        mode="fully_local",
        stt=STTConfig(
            provider="whisper-tiny",
            base_model="tiny",
            location="local",
        ),
        policy=DataPolicy(),
        meta={"local_provider": "whisper-tiny", "cloud_provider": "openai-whisper-1"},
    )


def test_apply_stt_mode_cloud():
    p = apply_stt_mode(_base(), "cloud")
    assert p.stt.location == "cloud"
    assert p.mode == "cloud_stt"
    assert p.policy.allow_cloud_audio is True
    assert p.stt.provider == "openai-whisper-1"


def test_apply_stt_mode_local_roundtrip():
    p = apply_stt_mode(apply_stt_mode(_base(), "cloud"), "local")
    assert p.stt.location == "local"
    assert p.mode == "fully_local"
    assert p.policy.allow_cloud_audio is False
    assert p.stt.provider == "whisper-tiny"
