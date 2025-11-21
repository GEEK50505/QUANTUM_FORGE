"""Compatibility shim for `backend.simulation.classical_sim.xtb_runner`.

This file is intentionally minimal: it re-exports the compatibility
runner from `backend.core.compat` so legacy import paths continue to
work while the implementation lives in `backend.core`.

Backups:
- Original implementation copied to
  `backend/legacy/simulation/classical_sim/xtb_runner.py`.
- A local backup created at
  `backend/simulation/classical_sim/xtb_runner.py.bak`.
"""

from backend.core.compat import XTBRunner

__all__ = ["XTBRunner"]

