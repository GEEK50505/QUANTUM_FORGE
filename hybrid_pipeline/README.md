# Hybrid Pipeline

## Overview

This directory previously contained hybrid pipeline code but has been consolidated into the backend package.

**⚠️ NOTE: This directory is deprecated. The actual implementation is now located in `backend/simulation/hybrid_pipeline/`.**

## Migration

All hybrid pipeline code has been moved to:
```
backend/simulation/hybrid_pipeline/
```

## Import Path

To use the hybrid simulator, import from the backend package:
```python
from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator
```

## Status

This directory will be removed in a future release. Please update your imports to use the new location.