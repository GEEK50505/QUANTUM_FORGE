Backend core modules: runners, parsers, and IO

This folder contains the canonical implementations and helpers for xTB
integration used by the rest of the application. Keep these rules in mind:

- `xtb_runner.py` contains the canonical, programmatic runner used by the
  API and JobManager. It expects an `XTBConfig` instance and a logger.
- `parsers.py` contains `XTBLogParser` which produces a stable dict of
  parsed results and preserves backward-compatible aliases used by older
  scripts/tests.
- `io.py` centralizes file-hash computation and JSON persistence helpers.
- `compat.py` provides a compatibility adapter exposing the legacy
  `XTBRunner(input_xyz, workdir, logger)` public API while delegating to
  the canonical runner internally. Scripts and CLI tools should import
  `backend.core.compat.XTBRunner` to keep behaviour stable during refactors.

Job-id contract
---------------
- JobManager (API) generates job IDs of the form
  `<molecule>_<timestamp>_<short-uuid>` and stores job metadata under
  `JOBS_DIR/<job_id>/`.
- Scripts using the classical compat runner may generate `xtb_job_...`
  IDs; these are local to script runs. The canonical runner accepts a
  job_id passed in for integration with JobManager.

Logging
-------
Use `backend.core.logging.get_logger(name)` across `backend.core` and
`backend.api` modules to get a consistent logger configuration (the
function delegates to `backend.config.get_logger` under the hood).

Migration guidance
------------------
- Keep the compatibility adapter (`compat.py`) as the single public
  entrypoint for scripts while consolidating logic into the canonical
  runner. Remove duplicates from legacy locations (e.g.,
  `backend/simulation/classical_sim`) only after tests are green.
