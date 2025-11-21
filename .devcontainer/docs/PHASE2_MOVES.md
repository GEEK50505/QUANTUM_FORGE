# Phase 2 Moves — Completed & Planned

This document records the safe, non-destructive refactor moves performed and the remaining planned items.

Completed (safe, reversible moves)

- Centralized `XTBRunner` implementation into `backend/core/xtb_runner.py`.
  - Created `backend/core/compat.py` exposing a backward-compatible `XTBRunner` API.
  - Added thin shim `backend/simulation/classical_sim/xtb_runner.py` that re-exports `backend.core.compat.XTBRunner`.
  - Archived the original implementation in `backend/legacy/simulation/classical_sim/xtb_runner.py` and created `.bak` snapshots.
- Centralized `XTBLogParser` in `backend/core/parsers.py` and added compatibility shim `backend/simulation/classical_sim/xtb_parser.py`.
- Added `backend/core/io.py` helpers and moved internal uses to canonical modules where needed.
- Created non-destructive backups for edited files (.bak, .autodoc.bak) and documented the approach in `docs/PHASE2_MOVE_PLAN.md`.
- Inserted standardized file header templates in frontend TypeScript files (script available at `scripts/add_frontend_headers.py`).
- Installed `ruff` in the project venv and auto-fixed a large portion of lint issues; remaining issues were fixed by targeted edits.
- Fixed small TypeScript issues (Table API, Button size prop, status enum casing) and ensured `tsc --noEmit` passes for the frontend.

Remaining / Planned

- Identify any remaining duplicate modules outside `backend/core` and apply the same safe move pattern (archive -> shim -> tests).
- Optionally remove `backend/legacy` entries after a monitoring period and CI green runs.

Rollback procedure

1. Revert the commit that contains a problematic move (each move is committed atomically).
2. If necessary, restore the archived file from `backend/legacy/`.

If you'd like, I can now proceed to perform the next safe atomic move (pick one file/group and run the archive+shim+pytest sequence).
