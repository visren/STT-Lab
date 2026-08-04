"""On-device dictation history with simple retention policy."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from .config import HISTORY_DIR, ensure_dirs
from .policy import DataPolicy, PrivacyTrace


def _history_path() -> Path:
    ensure_dirs()
    return HISTORY_DIR / "dictation.jsonl"


def append_dictation(
    *,
    text: str,
    profile_id: str,
    trace: PrivacyTrace,
    policy: DataPolicy,
    audio_path: str | None = None,
) -> dict[str, Any] | None:
    if not policy.store_transcript_locally:
        return None
    row = {
        "id": uuid.uuid4().hex,
        "ts": time.time(),
        "profile_id": profile_id,
        "text": text,
        "audio_path": audio_path if policy.store_audio_locally else None,
        "trace": trace.model_dump(),
    }
    path = _history_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    prune_history(policy)
    return row


def prune_history(policy: DataPolicy) -> int:
    """Delete history rows older than retention. Returns removed count."""
    retention = (policy.retention or "forever").strip().lower()
    if retention in {"forever", "none", ""}:
        if retention == "none":
            path = _history_path()
            if path.exists():
                path.unlink()
                return 1
        return 0
    if not retention.startswith("days:"):
        return 0
    try:
        days = int(retention.split(":", 1)[1])
    except ValueError:
        return 0
    cutoff = time.time() - days * 86400
    path = _history_path()
    if not path.exists():
        return 0
    kept: list[str] = []
    removed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            removed += 1
            continue
        if float(row.get("ts", 0)) >= cutoff:
            kept.append(json.dumps(row))
        else:
            removed += 1
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    return removed
