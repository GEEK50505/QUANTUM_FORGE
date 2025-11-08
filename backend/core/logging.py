"""Small logging compatibility wrapper for backend modules.

Expose a single `get_logger(name)` function so modules import a stable
logger factory during the refactor. This delegates to
`backend.config.get_logger` (the existing project logger) to avoid
changing runtime behaviour.
"""
import logging

from backend.config import get_logger as _project_get_logger


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given name.

    This wrapper centralizes the import point so callers can import from
    `backend.core.logging` instead of scattering references to
    `backend.config.get_logger` or other factories.
    """
    return _project_get_logger(name)
