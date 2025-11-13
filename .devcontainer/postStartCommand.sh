#!/usr/bin/env bash
set -euo pipefail
echo "Devcontainer post-start: ensuring venv activation is possible"
cd /workspace
if [ -f .venv/bin/activate ]; then
  echo "Virtualenv available at .venv"
else
  echo "Warning: virtualenv not found at .venv"
fi

# Ensure the workspace runs and jobs directories are writable by the vscode user
echo "Ensuring /workspace/runs and /workspace/jobs are owned by vscode"
chown -R vscode:vscode /workspace/runs 2>/dev/null || true
chown -R vscode:vscode /workspace/jobs 2>/dev/null || true

# If a Miniconda volume is mounted at /opt/miniconda ensure permissions are usable
if [ -d /opt/miniconda ]; then
  echo "Fixing ownership of /opt/miniconda for dev usage"
  chown -R root:root /opt/miniconda || true
  # make sure the vscode account can still read/execute conda environment files
  chmod -R a+rX /opt/miniconda || true
fi

  # Ensure logs dir exists and is writable
  mkdir -p /workspace/logs
  chown -R vscode:vscode /workspace/logs || true

  # Helper to start a command as the vscode user if it's not already running
  run_if_missing() {
    local grep_pat="$1"; shift
    local cmd="$@"
    if ! pgrep -f "${grep_pat}" >/dev/null 2>&1; then
      echo "Starting: ${cmd}"
      su -s /bin/bash -c "${cmd}" vscode || true
    else
      echo "Process matching '${grep_pat}' already running"
    fi
  }

  # Start backend (uvicorn) and frontend (vite) as the vscode user in the background
  run_if_missing "uvicorn backend.api.main:app" "cd /workspace && nohup python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &"
  run_if_missing "vite" "cd /workspace/frontend && nohup env NODE_OPTIONS=--max-old-space-size=2048 npm run dev > /workspace/logs/vite.log 2>&1 &"

  echo "postStartCommand finished"
