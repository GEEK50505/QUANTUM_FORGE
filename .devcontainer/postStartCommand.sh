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
