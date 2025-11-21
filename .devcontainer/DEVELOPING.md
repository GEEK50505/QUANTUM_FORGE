# Developing Quantum_Forge — Make dependencies persistent

This document explains how to create a persistent local development environment so you don't have to reinstall dependencies after each reboot or VS Code restart.

Two recommended approaches:

1) Project-local virtual environment (easy)
- Creates a `.venv` folder in the repository root and installs Python packages there.
- Installs frontend `node_modules` under `frontend/` with `npm ci`.
- This `.venv` folder persists across reboots. Just avoid deleting it.

Quick setup (run once):
```bash
# from repo root
./scripts/setup_local_env.sh
```

Then in VS Code select the interpreter: `./.venv/bin/python` (the provided workspace settings will try to pick it automatically).

2) Reproducible container (recommended for teams / CI)
- Use a VS Code Dev Container (Docker) so the environment is containerized and reproducible across machines.
- Advantages: no local Python/node install needed, exact OS packages can be pinned, nothing gets removed after reboot.

If you want, I can add a `.devcontainer` configuration next (Dockerfile + devcontainer.json) that will build and cache all dependencies in a reproducible way.

Notes and tips
- Do not commit `.venv` or `node_modules` to Git. These are large and should be ignored. Use `requirements.txt` and `package-lock.json`/`pnpm-lock.yaml` for reproducible installs.
- If you see pip trying to build packages from source (sdist), installing `wheel` and having a compatible Python version usually allows pip to pick prebuilt wheels instead.
- If your system deletes `.venv` on reboot (e.g., ephemeral VM, or workspace mounted from a temporary location), use the devcontainer approach instead.
