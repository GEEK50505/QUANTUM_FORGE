#!/bin/bash
set -a
source /workspace/.env.backend
set +a
cd /workspace
exec python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
