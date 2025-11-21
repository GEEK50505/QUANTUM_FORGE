#!/usr/bin/env bash
set -euo pipefail
# Helper to run the worker inside the devcontainer.
# Usage (inside container): ./services/worker/run_in_devcontainer.sh

cd /workspace

# Activate the repository venv if present
if [ -f .venv/bin/activate ]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi

# Use python to safely load .env.backend and exec the worker
python - <<'PY'
from dotenv import dotenv_values
import os, runpy
cfg = dotenv_values('/workspace/.env.backend')
for k,v in cfg.items():
    if v is not None:
        os.environ[k]=v
runpy.run_path('/workspace/services/worker/worker.py', run_name='__main__')
PY
