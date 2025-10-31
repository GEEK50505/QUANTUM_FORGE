"""
Visualization Utilities for Quantum Forge

This module provides access to visualization tools
implemented in the backend package.

The actual implementation is located in:
    backend.simulation.utils.visualization

Import from the backend package instead:
    from backend.simulation.utils.visualization import SimulationVisualizer

This file is maintained for backward compatibility and to preserve git history.
"""

# Import the actual implementation from backend
try:
    from backend.simulation.utils.visualization import SimulationVisualizer
    __all__ = ['SimulationVisualizer']
except ImportError:
    # Fallback for development environments
    __all__ = []
