# Onboarding (quick start) — UNDER ACTIVE DEVELOPMENT

This onboarding doc is a short checklist to get a new contributor up and running. Everything is under active development; expect the commands and files to evolve.

1) Prerequisites
- Install Node.js (v18+ recommended) and npm
- Install Python 3.10+ and create a virtual environment

2) Get the code
- Clone the repo and open it in VS Code

3) Frontend
- cd frontend
- npm install
- npm run dev

4) Backend / Python
- python -m venv .venv
- .\.venv\Scripts\Activate
- pip install -r requirements.txt
- Run a small smoke import: python -c "import src.classical_sim" (adjust path as needed)

5) LLM / AI adapters
- See `backend/ai/README.md` and `docs/api_contract.md` for the current adapter interfaces.

If things break, open an issue or contact the maintainers. All modules are explicitly marked as "UNDER ACTIVE DEVELOPMENT".
