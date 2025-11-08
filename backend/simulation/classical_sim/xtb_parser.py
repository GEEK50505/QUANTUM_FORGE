"""
Parse xTB output logs with comprehensive logging.
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from backend.core.logger import setup_logger

"""
Compatibility shim for `XTBLogParser`.

This module now delegates to the canonical parser at `backend.core.parsers`.
Keeping this shim at the original import path preserves backwards
compatibility for scripts and tests while centralizing parsing logic.
"""

from backend.core.parsers import XTBLogParser as CanonicalXTBLogParser


# Re-export the canonical parser under the old name
class XTBLogParser(CanonicalXTBLogParser):
    """Thin subclass that preserves the original import path and name.

    It does not add behavior; it exists to keep older import locations
    working while code migrates to the canonical parser in
    `backend.core.parsers`.
    """
    pass