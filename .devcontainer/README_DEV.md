# Devcontainer for QUANTUM_FORGE

This repository includes a VS Code Dev Container configuration in `.devcontainer/`.

Overview:

- The container image installs Python 3.12, Node.js, and common build tools.
- A workspace-level virtualenv is created at `.venv` and Python dependencies are installed from `requirements.txt`.
- Frontend dependencies are installed under `frontend/` using `npm ci`.
- A named Docker volume `quantum_jobs` is mounted at `/workspace/jobs` so job artifacts persist across container restarts and host reboots.
- For local development, the repository contains `scripts/xtb_mock` and the devcontainer setup symlinks it into `/usr/local/bin/xtb` so xTB calls use the mock.

How to build and run locally (requires Docker):

```bash
# From repository root
docker build -f .devcontainer/Dockerfile -t quantum_forge_dev:latest .

# Run container with workspace bind mount and the persistent jobs volume
docker run -d \
  --name quantum_dev \
  -v "$(pwd)":/workspace \
  -v quantum_jobs:/workspace/jobs \
  -p 8000:8000 -p 5173:5173 -p 3000:3000 \
  quantum_forge_dev:latest

# Execute the post-create script (installs deps and links xtb mock)
docker exec -it quantum_dev /tmp/postCreateCommand.sh

# Enter the container
docker exec -it quantum_dev bash
# inside container
. .venv/bin/activate
python run_api.py --host 0.0.0.0 --port 8000
```

Notes:

- The `quantum_jobs` Docker volume ensures that `/workspace/jobs` persists even if the container is removed or the host reboots.
- If you have a real xTB binary and want to use it instead, replace the symlink at `/usr/local/bin/xtb` with the path to your binary.

Docker-based integration test (recommended)
-----------------------------------------

You can use the included `docker-compose.yml` at the repository root to build production-like images for the backend and frontend.

1. Build and start the backend container (it will mount `./jobs` so artifacts are written to your host):

```bash
docker compose -f docker-compose.yml up -d --build backend
```

2. Run the integration test that inserts a molecule and a calculation and simulates quality logging into Supabase:

```bash
./scripts/integration_test.sh
```

3. Inspect Supabase table counts (this will print the number of rows in relevant tables):

```bash
docker exec quantum_backend bash -lc "cd /app && PYTHONPATH=/app python3 - <<'PY'\nfrom backend.app.db.supabase_client import get_supabase_client\nc=get_supabase_client()\nprint('data_quality_metrics', len(c.get('data_quality_metrics')))\nprint('data_lineage', len(c.get('data_lineage')))\nprint('molecules', len(c.get('molecules')))\nprint('calculations', len(c.get('calculations')))\nPY"
```

Notes:

- This integration test is intentionally minimal: it demonstrates the full logging path without requiring the xTB binary.
- The frontend build in `docker-compose` is optional: if TypeScript build errors block the compose build on your workstation, start only the `backend` service as shown above.
