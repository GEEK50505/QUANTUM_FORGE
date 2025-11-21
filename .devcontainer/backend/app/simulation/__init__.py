"""
Compatibility re-exports for backend.simulation

This module provides lightweight re-exports of the main simulation
components to keep import paths stable while we consolidate modules.
"""

from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator
# Use canonical compat XTBRunner to avoid importing internal classical_sim module directly
from backend.core.compat import XTBRunner as ClassicalXTBRunner
from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver
from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator
from backend.core.parsers import XTBLogParser

__all__ = [
    "ClassicalSimulator",
    "ClassicalXTBRunner",
    "QuantumSolver",
    "HybridSimulator",
    "XTBLogParser",
]
