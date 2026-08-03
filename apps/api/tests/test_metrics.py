from app.services.metrics import compute_wer_cer, word_diff


def test_wer_perfect():
    wer_v, cer_v = compute_wer_cer("hello world", "hello world")
    assert wer_v == 0.0
    assert cer_v == 0.0


def test_wer_needs_reference():
    wer_v, cer_v = compute_wer_cer(None, "hello")
    assert wer_v is None
    assert cer_v is None


def test_word_diff_insert_delete():
    ops = word_diff("one two three", "one too three four")
    kinds = [o["op"] for o in ops]
    assert "equal" in kinds
    assert "insert" in kinds or "delete" in kinds
