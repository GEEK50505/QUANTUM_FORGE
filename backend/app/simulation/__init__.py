"""
Compatibility re-exports for backend.simulation

This module provides lightweight re-exports of the main simulation
components to keep import paths stable while we consolidate modules.
"""

from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator
from backend.simulation.classical_sim.xtb_runner import XTBRunner as ClassicalXTBRunner
from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver
from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator

__all__ = [
    "ClassicalSimulator",
    "ClassicalXTBRunner",
    "QuantumSolver",
    "HybridSimulator",
]
