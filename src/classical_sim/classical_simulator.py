"""
Classical Simulator Module for Quantum Forge

This module provides access to the classical molecular dynamics simulator
implemented in the backend package.

The actual implementation is located in:
    backend.simulation.classical_sim.classical_simulator

Import from the backend package instead:
    from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator

This file is maintained for backward compatibility and to preserve git history.
"""

# Import the actual implementation from backend
try:
    from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator
    __all__ = ['ClassicalSimulator']
except ImportError:
    # Fallback for development environments
    __all__ = []
