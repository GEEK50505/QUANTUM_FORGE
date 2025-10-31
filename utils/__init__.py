"""
Compatibility shim package for `utils` (simulation utilities).

Forwards to `backend.simulation.utils`.
"""
from backend.simulation.utils.visualization import *

__all__ = [name for name in globals() if not name.startswith("_")]
