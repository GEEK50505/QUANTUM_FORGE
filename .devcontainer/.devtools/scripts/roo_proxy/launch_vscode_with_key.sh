#!/usr/bin/env bash
# Launch VS Code with the current best OpenRouter key loaded into the process
# This ensures extensions that read OPENROUTER_API_KEY at activation pick up the rotated key.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/scripts/roo_proxy/.env"

if [ -f "$ENV_FILE" ]; then
  # Export lines like OPENROUTER_API_KEY=... into this shell before launching code
  # We only export known variables to avoid side-effects
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      OPENROUTER_API_KEY=*) export "$line" ;;
      ROO_CODE_API_KEY=*) export "$line" ;;
      *) ;;
    esac
  done < "$ENV_FILE"
else
  echo "Warning: $ENV_FILE not found. No key will be exported." >&2
fi

# Launch VS Code in the repository root so it inherits these env vars
code "$ROOT_DIR"
