#!/usr/bin/env bash
set -euo pipefail
cd /workspace
export PYTHONPATH="/workspace:${PYTHONPATH:-}"
echo "STT model-lab ready."
echo "  python -m envs.model_lab.cli --help"
exec "$@"
