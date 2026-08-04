#!/usr/bin/env bash
set -euo pipefail

cd /workspace
export PYTHONPATH="/workspace:${PYTHONPATH:-}"
export HF_HOME="${HF_HOME:-/home/lab/.cache/huggingface}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/home/lab/.cache}"

cmd="${1:-bash}"

case "$cmd" in
  doctor)
    shift || true
    python - <<'PY'
import importlib
import platform
import sys

mods = [
    "stt_lab",
    "faster_whisper",
    "torch",
    "transformers",
    "peft",
    "minio",
    "sqlalchemy",
]
print(f"python {sys.version.split()[0]}  ({platform.machine()})")
for name in mods:
    try:
        m = importlib.import_module(name)
        ver = getattr(m, "__version__", "?")
        print(f"  ok  {name}={ver}")
    except Exception as exc:
        print(f"  FAIL {name}: {exc}")
        sys.exit(1)
print("model-lab doctor: healthy")
PY
    ;;
  models|smoke|finetune)
    exec python -m envs.model_lab.cli "$@"
    ;;
  *)
    if [[ "${1:-}" != "bash" && "${1:-}" != "sh" && $# -gt 0 ]]; then
      echo "STT model-lab ready. Shortcuts: doctor | models | smoke | finetune"
    else
      echo "STT model-lab ready."
      echo "  model-lab-entry doctor"
      echo "  python -m envs.model_lab.cli --help"
    fi
    exec "$@"
    ;;
esac
