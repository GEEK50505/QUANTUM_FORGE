# Utilities

## Overview

This directory previously contained utility code but has been consolidated into the backend package.

**⚠️ NOTE: This directory is deprecated. The actual implementation is now located in `backend/simulation/utils/`.**

## Migration

All utility code has been moved to:
```
backend/simulation/utils/
```

## Import Path

To use the visualization utilities, import from the backend package:
```python
from backend.simulation.utils.visualization import SimulationVisualizer
```

## Status

This directory will be removed in a future release. Please update your imports to use the new location.