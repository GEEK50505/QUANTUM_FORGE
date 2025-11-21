"""
Archival snapshot of the original classical_sim xtb_runner.

Saved as part of Phase 2A dry-run moves. This file is a verbatim copy
of the pre-refactor implementation and exists to make rollbacks simple.

This compatibility shim forwards to `backend.core.compat.XTBRunner`.
The implementation below is intentionally small and re-uses the
canonical adapter; this file is a safe archive and compatibility layer.
"""
from pathlib import Path
from typing import Dict, Optional, Any

from backend.core.compat import XTBRunner as CompatXTBRunner


class XTBRunner:
    """Thin shim around `backend.core.compat.XTBRunner`.

    Methods match the legacy interface so callers can migrate safely.
    """

    def __init__(self, input_xyz: str, workdir: str = "./runs", logger: Optional[object] = None):
        self._runner = CompatXTBRunner(input_xyz, workdir, logger)

    def generate_job_id(self) -> str:
        return self._runner.generate_job_id()

    def validate_input_file(self) -> bool:
        return self._runner.validate_input_file()

    def run(self, optimization_level: str = "tight", max_retries: Optional[int] = None) -> Dict[str, Any]:
        return self._runner.run(optimization_level=optimization_level, max_retries=max_retries)

    def save_results(self, results: Dict[str, Any], output_dir: Optional[str] = None) -> Path:
        return self._runner.save_results(results, output_dir)

    def save_metadata(self, results: Dict[str, Any], output_dir: Optional[str] = None) -> Path:
        return self._runner.save_metadata(results, output_dir)

    def compute_file_hash(self, filepath: str) -> str:
        # compat exposes compute_file_hash as an instance helper
        return self._runner.compute_file_hash(filepath)

