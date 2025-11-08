# Phase 2 — Safe Reorganization Move Plan (detailed)

Goal
----
Perform a non-destructive reorganization of the repository to reduce duplication, move canonical code into stable locations, and provide shims that preserve public import paths so existing scripts, tests, and CI continue to work.

High-level constraints
- Make no breaking changes to public Python import paths expected by scripts and tests. Use shims where necessary.
- Perform moves in small, verifiable steps. After each step run a small set of smoke checks and the full pytest suite.
- Keep backups or use git branches for all moves so changes are revertible.

Target structure (examples)
- backend/
  - core/             # canonical implementations (xtb_runner, parsers, io)
  - api/              # fastapi routes, job manager (uses JobStore)
  - db/               # JobStore and future DB adapters
  - legacy/           # moved legacy/duplicate implementations (shallow copies)
  - simulation/       # simulation entrypoints (thin shims pointing to core)

Planned file moves and shims (safe, step-by-step)

1) Canonicalization and shim creation (no moves yet)
   - Create explicit compatibility shims for public import locations that currently point to duplicate implementations.
     Example: ensure `backend/simulation/classical_sim/xtb_runner.py` is a 10-line shim that imports and delegates to `backend.core.compat.XTBRunner`.
   - Tests: run `pytest -q` (full) and verify everything passes (baseline). Commit shims.

2) Move duplicate files into a `backend/legacy/` subtree (non-destructive)
   - Move file: `backend/simulation/classical_sim/xtb_runner.py` -> `backend/legacy/simulation/classical_sim/xtb_runner.py`
   - Create shim at the original path with the previous content (thin import-and-delegate) so existing imports work.
   - Move other duplicates (if any) similarly, one file or logical group at a time.
   - Tests per-file/group:
     - Run `pytest -q`.
     - Run a targeted smoke script that invokes the moved module via both import paths (old and new) to verify parity.

3) Consolidate parsing & IO only after shims are in place
   - Confirm canonical modules exist at `backend/core/parsers.py` and `backend/core/io.py` and are the single source-of-truth.
   - Replace internal references progressively to use `backend.core.parsers` and `backend.core.io`.
   - Tests: run `pytest -q` and targeted tests for parsing and IO.

4) Move higher-level code (job manager, runner impl) to canonical locations
   - Move any remaining duplicates of xtb runner implementations into `backend/legacy/`.
   - Update imports in internal modules to use canonical `backend.core.xtb_runner` and `backend.core.compat`.
   - Keep a minimal shim at the old path to import & re-export the canonical class for backward compatibility.
   - Tests: `pytest -q`, run `scripts/*` CLI scripts, and smoke the API endpoints if possible (local uvicorn run).

5) Cleanup
   - After several CI-green runs and a short period of monitoring, remove legacy files from the main tree (move from `backend/legacy/` to the `archive/` branch first if desired).
   - Add `backend/legacy/` to the repository docs and ensure `README` points at it.

Per-step checks and rollback guidance
- Always create a short commit that contains the move + shim in one atomic change. This makes `git revert` straightforward.
- After each change, run these checks:
  1. `pytest -q` (full test suite)
  2. Smoke import tests (small Python snippet that imports both new and old paths and calls a representative method)
  3. Linting/phplint (if in CI)
- If tests fail, revert the commit, investigate, and apply a smaller change.

Detailed example: moving `classical_sim/xtb_runner.py`
1. Create shim at `backend/simulation/classical_sim/xtb_runner.py`:
   - Content: import canonical from `backend.core.compat` and re-export the class.
2. Move original implementation to `backend/legacy/simulation/classical_sim/xtb_runner.py`.
3. Commit with message: "Move classical runner to backend/legacy and add shim to preserve import path".
4. Run `pytest -q` and targeted smoke tests.
5. If green, push; if failing, revert and fix.

Testing matrix and smoke tests
- Unit tests: `pytest -q` (full).
- Targeted smoke scripts:
  - basic import: `python -c "from backend.simulation.classical_sim.xtb_runner import XTBRunner; print(XTBRunner)"`
  - run a minimal `XTBRunner` invocation in a tmpdir to ensure run() works.

Risk profile and mitigations
- Risk: Breaking imports in external scripts (mitigation: preserve shims and run full test suite after each change).
- Risk: Hidden duplicate behavior (mitigation: create `backend/legacy/` as read-only archive for comparison; never delete until verified).

Rollout schedule
- Week 1: prepare shims and move low-risk files (parsers/io duplicates). Run full test suite after each move.
- Week 2: move higher-level runners behind shims. Run integration smoke tests and API routes.
- Week 3: cleanup and delete legacy code after sign-off.

Acceptance criteria
- All tests pass with unchanged public import paths.
- No behavioral regressions in the API or scripts.
- Clear `backend/legacy/` archive exists for any removed code.

Notes
- Keep changes small and continuously tested. If you're uncertain about a change, open a PR and request a short-time feature branch for team verification.

Contact
- If you want, I can start by performing step 1 (generate shims and verify) for the xtb runner in a safe commit. Approve and I'll execute.
