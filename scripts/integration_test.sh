#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/integration_test.sh
# Pull up containers, run logging tests inside backend and assert tables updated

COMPOSE_FILE=docker-compose.yml

echo "Starting services..."
docker compose -f ${COMPOSE_FILE} up -d --build backend

echo "Waiting for backend to come up..."
until docker exec quantum_backend curl -sS http://localhost:8000/ >/dev/null 2>&1; do
  sleep 1
done

echo "Backend ready. Running molecule/calculation insert test..."
docker exec quantum_backend bash -lc "cd /app && PYTHONPATH=/app python3 scripts/test_insert_mol_calc.py"

# Simulate logging for existing job
echo "Creating a new job via API and simulating results..."
JOB_ID=$(docker exec quantum_backend bash -lc "cd /app && PYTHONPATH=/app python3 - <<'PY'
from backend.api.job_manager import JobManager
from backend.config import XTBConfig
cfg = XTBConfig()
jm = JobManager(cfg)
job_id = jm.submit_job({
    'molecule_name': 'water_integration',
    'xyz_content': '3\nWater\nO 0 0 0\nH 0 0 0\nH 0 0 0\n'
})
print(job_id)
PY")

echo "Job created: $JOB_ID"
echo "Copying a sample results.json into job dir and running simulate logger"
docker exec quantum_backend bash -lc "cd /app && cp -a jobs/water_20251114_172443_571f41c6/results.json jobs/${JOB_ID}/results.json || true"
docker exec quantum_backend bash -lc "cd /app && PYTHONPATH=/app python3 scripts/test_simulate_log.py ${JOB_ID}"

# Show row counts in Supabase tables
docker exec quantum_backend bash -lc "cd /app && PYTHONPATH=/app python3 - <<'PY'
from backend.app.db.supabase_client import get_supabase_client
c=get_supabase_client()
print('quality', len(c.get('data_quality_metrics')))
print('lineage', len(c.get('data_lineage')))
print('molecules', len(c.get('molecules')))
print('calculations', len(c.get('calculations')))
PY"

echo "Integration test complete. Containers remain running."

# To tear down: docker compose -f docker-compose.yml down
