from __future__ import annotations

from typing import Any

from jiwer import cer, wer


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def compute_wer_cer(reference: str | None, hypothesis: str) -> tuple[float | None, float | None]:
    if reference is None or not reference.strip():
        return None, None
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)
    if not ref:
        return None, None
    if not hyp:
        return 1.0, 1.0
    try:
        return float(wer(ref, hyp)), float(cer(ref, hyp))
    except Exception:
        return None, None


def word_diff(reference: str | None, hypothesis: str) -> list[dict[str, Any]]:
    """Simple word-level ops: equal | insert | delete | replace."""
    if reference is None or not reference.strip():
        words = hypothesis.split()
        return [{"op": "insert", "text": w} for w in words] if words else []

    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()

    # Classic LCS-based alignment
    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if ref_words[i] == hyp_words[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    ops: list[dict[str, Any]] = []
    i = j = 0
    while i < n and j < m:
        if ref_words[i] == hyp_words[j]:
            ops.append({"op": "equal", "text": hyp_words[j]})
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            ops.append({"op": "delete", "text": ref_words[i]})
            i += 1
        else:
            ops.append({"op": "insert", "text": hyp_words[j]})
            j += 1
    while i < n:
        ops.append({"op": "delete", "text": ref_words[i]})
        i += 1
    while j < m:
        ops.append({"op": "insert", "text": hyp_words[j]})
        j += 1
    return ops
