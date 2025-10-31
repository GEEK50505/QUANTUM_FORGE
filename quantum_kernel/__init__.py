"""
Compatibility shim package for `quantum_kernel`.

Forwards imports to `backend.simulation.quantum_kernel`.
"""
from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver

__all__ = ["QuantumSolver"]
