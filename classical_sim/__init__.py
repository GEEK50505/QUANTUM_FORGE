"""
Compatibility shim package for `classical_sim`.

This module forwards imports to `backend.simulation.classical_sim` so
existing code that imports `classical_sim.*` continues to work while the
canonical implementation lives under `backend.simulation`.
"""
from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator

__all__ = ["ClassicalSimulator"]
