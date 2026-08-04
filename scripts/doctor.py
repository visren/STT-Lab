#!/usr/bin/env python3
"""Local environment sanity checks for STT Lab."""

from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print(f"root: {ROOT}")
    print(f"python: {sys.version.split()[0]} ({platform.platform()})")
    sys.path.insert(0, str(ROOT))

    required = [
        "stt_lab",
        "stt_lab.pipeline",
        "stt_lab.vault",
        "stt_lab.cloud_finetune",
        "apps.dictation.app",
        "envs.model_lab.cli",
    ]
    optional = [
        ("torch", "ML"),
        ("faster_whisper", "local STT"),
        ("sounddevice", "dictation mic"),
        ("pynput", "dictation hotkeys"),
        ("jupyterlab", "research notebooks"),
    ]

    failed = False
    for name in required:
        try:
            importlib.import_module(name)
            print(f"  ok   {name}")
        except Exception as exc:
            print(f"  FAIL {name}: {exc}")
            failed = True

    for name, role in optional:
        try:
            mod = importlib.import_module(name)
            ver = getattr(mod, "__version__", "?")
            print(f"  ok   {name}={ver} ({role})")
        except Exception as exc:
            print(f"  skip {name} ({role}): {exc}")

    profiles = ROOT / "data" / "profiles" / "demo-local.json"
    print(f"  {'ok' if profiles.exists() else 'FAIL'}  demo profile: {profiles}")
    if not profiles.exists():
        failed = True

    if failed:
        print("doctor: FAILED")
        return 1
    print("doctor: healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
