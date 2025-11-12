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
