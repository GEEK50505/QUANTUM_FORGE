"""
Quantum Solver Module for Quantum Forge

This module provides access to the quantum mechanical solver
implemented in the backend package.

The actual implementation is located in:
    backend.simulation.quantum_kernel.quantum_solver

Import from the backend package instead:
    from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver

This file is maintained for backward compatibility and to preserve git history.
"""

# Import the actual implementation from backend
try:
    from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver
    __all__ = ['QuantumSolver']
except ImportError:
    # Fallback for development environments
    __all__ = []
