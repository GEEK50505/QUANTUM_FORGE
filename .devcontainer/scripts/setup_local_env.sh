#!/usr/bin/env bash
# Create and populate a project-local Python virtualenv (.venv)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Setting up project-local virtualenv at .venv"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

echo "Activating .venv"
source .venv/bin/activate

echo "Upgrading pip and installing requirements"
pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
  pip install -r requirements.txt || true
else
  echo "requirements.txt not found; skipping python deps install"
fi

echo "Installing frontend dependencies (npm)"
if command -v npm >/dev/null 2>&1 && [ -d frontend ]; then
  (cd frontend && npm ci)
else
  echo "npm not found or frontend/ missing; please install node and run 'cd frontend && npm ci'"
fi

echo "Local environment setup complete. In VS Code, select interpreter: ./.venv/bin/python"
echo "Note: .venv is persistent across reboots; do not delete it unless you want to recreate the env."
