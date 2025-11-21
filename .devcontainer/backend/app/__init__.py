"""
backend.app package

This package acts as a compatibility shim while the repository is being
reorganized. It exposes stable import paths for the running application so
we can move modules underneath `backend/` incrementally without breaking
imports in scripts, tests, and the frontend.

Do not add heavy imports here to avoid circular import issues; this file
keeps the package present for Python's import system.

AUTHOR: Quantum_Forge Team
LAST_MODIFIED: 2025-11-08
"""

__all__ = ["api", "core", "simulation"]
