"""
ARCHIVE: backup of `backend/core/compat.py` created before Phase 2 moves.

This is a snapshot of the compatibility adapter preserved under
`backend/legacy` for comparison and rollback.
"""

#!/usr/bin/env python3

from pathlib import Path
from typing import Dict, Optional
import json
import logging

from backend.config import XTBConfig, get_logger
from backend.core.xtb_runner import XTBRunner as CanonicalXTBRunner


class XTBRunner:
    """(Snapshot) Adapter that mimics the classical runner interface.
    See `backend/core/compat.py` for the canonical compatibility adapter.
    """

    def __init__(self, input_xyz: str, workdir: str = './runs', logger: Optional[logging.Logger] = None):
        self.input_xyz = Path(input_xyz)
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or get_logger(__name__)
        self.logger.debug(f"Initializing XTBRunner with input: {input_xyz}")
        self.logger.info(f"Working directory: {workdir}")
        self.job_id = self.generate_job_id()
        try:
            self.logger.info(f"Generated job ID: {self.job_id}")
        except Exception:
            self.logger.debug("Generated job ID created")
        self.logger.debug(f"Compat XTBRunner init: {self.input_xyz} -> {self.workdir}")

    def compute_file_hash(self, filepath: str) -> str:
        import hashlib
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        digest = h.hexdigest()
        try:
            self.logger.debug(f"Computed hash for {filepath}: {digest[:10]}...")
        except Exception:
            pass
        return digest

    def generate_job_id(self) -> str:
        import time
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        name = self.input_xyz.stem if self.input_xyz else ''
        if name:
            return f"xtb_job_{name}_{timestamp}"
        return f"xtb_job_{timestamp}"

    def validate_input_file(self) -> bool:
        try:
            if not self.input_xyz.exists() or not self.input_xyz.is_file():
                return False
            with open(self.input_xyz, 'r') as f:
                lines = f.readlines()
            if len(lines) < 2:
                return False
            try:
                atom_count = int(lines[0].strip())
            except ValueError:
                return False
            if len(lines) < atom_count + 2:
                return False
            return True
        except Exception:
            return False

    def run(self, optimization_level: str = 'tight', max_retries: int = None) -> Dict:
        config = XTBConfig()
        config.WORKDIR = str(self.workdir)
        canonical = CanonicalXTBRunner(config, self.logger)
        results = canonical.execute(str(self.input_xyz), self.job_id, optimization_level)
        results.setdefault('job_id', self.job_id)
        return results

    def save_results(self, results: Dict, output_dir: str = None) -> Path:
        if output_dir is None:
            output_dir = './results'
        output_path = Path(output_dir) / f"{self.job_id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        self.logger.debug(f"Saved results to {output_path}")
        return output_path

    def save_metadata(self, results: Dict, output_dir: str = None) -> Path:
        if output_dir is None:
            output_dir = './results'
        metadata = {
            'job_id': self.job_id,
            'input_file': str(self.input_xyz),
            'success': results.get('success', False),
            'energy': results.get('energy'),
        }
        metadata_path = Path(output_dir) / f"{self.job_id}_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.logger.debug(f"Saved metadata to {metadata_path}")
        return metadata_path
