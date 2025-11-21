"""
Compatibility re-exports for backend.core

This module re-exports important symbols from `backend.core` so code can
import from `backend.app.core` while we transition the package layout.

Keep this file minimal to avoid heavy import-side effects.
"""

from backend.core.logger import setup_logger, log_execution_time
from backend.core.xtb_runner import XTBRunner
from backend.core.config import XTBConfig, AppConfig, get_logger

__all__ = [
    "setup_logger",
    "log_execution_time",
    "XTBRunner",
    "XTBConfig",
    "AppConfig",
    "get_logger",
]
