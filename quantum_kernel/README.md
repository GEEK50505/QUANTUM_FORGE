# Quantum Kernel

## Overview

This directory previously contained quantum kernel code but has been consolidated into the backend package.

**⚠️ NOTE: This directory is deprecated. The actual implementation is now located in `backend/simulation/quantum_kernel/`.**

## Migration

All quantum kernel code has been moved to:
```
backend/simulation/quantum_kernel/
```

## Import Path

To use the quantum solver, import from the backend package:
```python
from backend.simulation.quantum_kernel.quantum_solver import QuantumSolver
```

## Status

This directory will be removed in a future release. Please update your imports to use the new location.