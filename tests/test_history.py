from stt_lab.history import append_dictation, prune_history
from stt_lab.policy import DataPolicy, PrivacyTrace


def test_history_append_and_prune(monkeypatch, tmp_path):
    from stt_lab import history as hist
    from stt_lab import config

    monkeypatch.setattr(config, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(hist, "HISTORY_DIR", tmp_path)

    policy = DataPolicy(store_transcript_locally=True, retention="days:30")
    trace = PrivacyTrace(mode="fully_local", stt_location="local")
    row = append_dictation(
        text="hello",
        profile_id="demo",
        trace=trace,
        policy=policy,
    )
    assert row is not None
    assert (tmp_path / "dictation.jsonl").exists()
    assert prune_history(policy) == 0
