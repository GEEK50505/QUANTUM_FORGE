# Setup Guide — Quantum_Forge

This guide shows how to prepare a development environment for the project.
It focuses on Ubuntu/Linux (developer's OS) and assumes you have Git and
Python 3.10+ installed.

1) Clone the repository

   git clone <repo-url>
   cd QUANTUM_FORGE

2) Create a Python virtual environment

   python3 -m venv .venv
   source .venv/bin/activate

3) Install Python dependencies

   pip install -r requirements.txt

4) Install xTB (system dependency)

   Follow official xTB instructions: https://xtb-docs.readthedocs.io/
   Ensure `xtb` is on your PATH (or update backend config to the absolute path)

5) Start backend dev server

   ./run_dev_server.sh

6) Start frontend dev server

   cd frontend
   npm install
   npm run dev

7) Run tests

   pytest -q

Notes:
- Environment variables are read from `.env`. Do NOT commit secrets.
- For reproducible dev containers, see `.devcontainer/` configuration.
