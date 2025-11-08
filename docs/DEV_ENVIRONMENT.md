# Developer environment setup (local)

This document describes how to set up a reproducible local development environment for the QUANTUM_FORGE repository.

Prerequisites
- Linux or macOS (tested locally)
- Python 3.12 (or compatible Python 3.10+)
- Node.js + npm (for frontend dev server)

Python environment (recommended)
1. Create a virtual environment in the repo root (optional if `.venv` already exists):

```bash
python3 -m venv .venv
```

2. Activate the venv (bash):

```bash
. .venv/bin/activate
```

3. Upgrade pip and install Python dependencies:

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

4. Install developer tooling (optional but recommended):

```bash
.venv/bin/python -m pip install ruff
```

Frontend (Node)
1. Change to `frontend/` and install dependencies:

```bash
cd frontend
npm ci
```

2. Run the Vite dev server:

```bash
npm run dev
```

Useful commands
- Run Python tests:

```bash
.venv/bin/pytest -q
```

- Run TypeScript no-emit check (from repo root or `frontend/`):

```bash
cd frontend && npx -p typescript@5 tsc -p tsconfig.json --noEmit
```

- Run ruff lint check across backend:

```bash
.venv/bin/ruff check backend scripts
```

- Insert standardized headers in frontend source files (dry-run first):

```bash
python3 scripts/add_frontend_headers.py --root frontend/src --extensions .ts .tsx --dry-run
python3 scripts/add_frontend_headers.py --root frontend/src --extensions .ts .tsx
```

Dev Container (optional)
------------------------
We provide a VS Code Dev Container configuration for an easy reproducible developer environment. The devcontainer will provision Python 3.12 and Node 18, create a `.venv`, install Python requirements, and run `npm ci` in the `frontend` folder.

To use it:

```bash
# In VS Code: Command Palette -> Remote-Containers: Open Folder in Container...
# or use the Reopen in Container command when prompted.
```

The `postCreateCommand` will run automatically and set up:
- `.venv` virtual environment with `requirements.txt` installed
- frontend dependencies installed via `npm ci`

If you prefer a manual flow instead of using the devcontainer, follow the Python and Frontend sections above.

Notes & safety
- The repo uses a non-destructive Phase 2 refactor pattern: original files moved to `backend/legacy/` and small shims are left behind to preserve import paths.
- Always run the test suite after making backend changes.

If you'd like, I can add a `devcontainer` or `docker` setup as a follow-up.
