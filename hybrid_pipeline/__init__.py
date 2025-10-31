"""
Compatibility shim package for `hybrid_pipeline`.

Forwards imports to `backend.simulation.hybrid_pipeline` so existing imports
keep working while canonical code lives under `backend/simulation`.
"""
from backend.simulation.hybrid_pipeline.hybrid_simulator import HybridSimulator

__all__ = ["HybridSimulator"]
