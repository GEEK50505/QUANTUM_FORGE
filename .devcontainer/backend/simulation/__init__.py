# Quantum Forge - Main Package Init
# Author: Qwen 3 Coder
# Description: Package initialization for Quantum Forge
# --------------------------------------------------------------

# ============================================================
# Package Purpose: Initialize the Quantum Forge package
# What this block does: Makes modules importable
# How it fits into the hybrid simulation pipeline: 
#   - Provides clean import structure for all modules
#   - Enables modular development and testing
# ============================================================

"""
Quantum Forge Package Initialization

This file makes the Quantum Forge package importable and defines
the public API for the hybrid simulation platform.

Educational Note - Package Structure:
===================================
In Python, __init__.py files:
1. Make directories into importable packages
2. Define what gets imported with "from package import *"
3. Control the public API of the package
4. Enable clean module organization

For Quantum Forge, this structure allows:
- Clean imports: from quantum_forge import HybridSimulator
- Modular development: each component can be developed separately
- Easy testing: each module can be tested independently
- Clear organization: related functionality grouped together
"""

# Import key classes for easy access
from .classical_sim.classical_simulator import ClassicalSimulator
from .quantum_kernel.quantum_solver import QuantumSolver
from .hybrid_pipeline.hybrid_simulator import HybridSimulator
from .utils.visualization import SimulationVisualizer

# Define what gets imported with "from quantum_forge import *"
__all__ = [
    'ClassicalSimulator',
    'QuantumSolver', 
    'HybridSimulator',
    'SimulationVisualizer'
]

# Package version and metadata
__version__ = "0.1.0"
__author__ = "Quantum Forge Team"
__description__ = "Hybrid Quantum-Classical Simulation Platform"

# Print welcome message when package is imported
print(f"Quantum Forge v{__version__} loaded")
print("Ready for hybrid quantum-classical simulations!")
print("For educational use: Detailed notes in each module")

# ============================================================
# Package Summary:
# This init file makes Quantum Forge a proper Python package
# - Enables clean imports of all main components
# - Defines the public API for the platform
# - Provides package metadata and version info
# - Shows welcome message for user orientation
# ============================================================
