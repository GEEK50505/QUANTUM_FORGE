#!/usr/bin/env bash
set -euo pipefail
# apply_destructive_migration.sh
# Safely load variables from .env and run the destructive migration SQL

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
MIGRATION_FILE="$REPO_ROOT/deploy/migrations/20251119_002_force_hybrid_compat_schema.sql"

if [ ! -f "$ENV_FILE" ]; then
  echo ".env file not found at $ENV_FILE"
  exit 1
fi

echo "Loading environment from $ENV_FILE"
while IFS='=' read -r key value || [ -n "$key" ]; do
  # Trim whitespace
  key="$(echo "$key" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  # Skip comments and empty lines
  if [ -z "$key" ] || [[ "$key" =~ ^# ]]; then
    continue
  fi
  # Preserve the full value (may contain =)
  value="${value:-}"
  export "$key=$value"
done < "$ENV_FILE"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL not set in $ENV_FILE. Aborting." >&2
  exit 2
fi

if [ ! -f "$MIGRATION_FILE" ]; then
  echo "Migration file not found: $MIGRATION_FILE" >&2
  exit 3
fi

echo "Applying destructive migration: $MIGRATION_FILE"
psql "$DATABASE_URL" -f "$MIGRATION_FILE"

echo "Migration completed."
