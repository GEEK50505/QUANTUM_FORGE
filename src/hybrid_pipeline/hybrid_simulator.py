"""
Hybrid Pipeline Module for Quantum Forge

This module provides access to the hybrid quantum-classical simulation pipeline
implemented in the backend package.

The actual implementation is located in:
    backend.simulation.hybrid_pipeline.hybrid_simulator

Import from the backend package instead:
    from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator

This file is maintained for backward compatibility and to preserve git history.
"""

# Import the actual implementation from backend
try:
    from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator
    __all__ = ['HybridSimulator']
except ImportError:
    # Fallback for development environments
    __all__ = []
