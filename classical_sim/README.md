# Classical Simulation

## Overview

This directory previously contained classical simulation code but has been consolidated into the backend package.

**⚠️ NOTE: This directory is deprecated. The actual implementation is now located in `backend/simulation/classical_sim/`.**

## Migration

All classical simulation code has been moved to:
```
backend/simulation/classical_sim/
```

## Import Path

To use the classical simulator, import from the backend package:
```python
from backend.simulation.classical_sim.classical_simulator import ClassicalSimulator
```

## Status

This directory will be removed in a future release. Please update your imports to use the new location.