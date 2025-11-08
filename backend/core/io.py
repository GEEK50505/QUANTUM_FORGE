"""
I/O helpers for saving xTB results and metadata.

This module centralizes result persistence used by multiple runners and the API.
Keeping a small, well-tested IO surface reduces duplication and makes it easier
to change storage strategies later (e.g., S3, DB, flat files).
"""
from pathlib import Path
import json
from typing import Any, Dict, Optional
import hashlib
from backend.core.logger import setup_logger


logger = setup_logger("core_io")


def compute_file_hash(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def save_results_json(results: Dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, sort_keys=True)
    logger.debug(f"Saved results JSON to {out_path}")
    return out_path


def load_results_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        logger.debug(f"Results file does not exist: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_metadata(metadata: Dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.debug(f"Saved metadata to {out_path}")
    return out_path
