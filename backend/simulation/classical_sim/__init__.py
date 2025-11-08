"""
Compatibility module for `backend.simulation.classical_sim`.

Historically this package exported local runner and parser implementations.
During consolidation we prefer the canonical implementations under
`backend.core`. To preserve the public API while centralizing code, re-export
the canonical implementations from `backend.core.compat` and
`backend.core.parsers`.
"""

from backend.core.compat import XTBRunner
from backend.core.parsers import XTBLogParser

__all__ = ['XTBRunner', 'XTBLogParser']
