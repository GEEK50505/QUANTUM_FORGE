import json
from pathlib import Path

import pytest

from backend.core.parsers import XTBLogParser
from backend.core.io import compute_file_hash, save_results_json, load_results_json


def test_parser_extracts_values(tmp_path: Path):
    sample = """
TOTAL ENERGY   -75.123456 Eh
Gradient norm  0.000123
HOMO-LUMO gap  5.4321 eV
HOMO/LUMO (eV): -10.5  -5.0
Total dipole moment  1.23 Debye
wall-time: 12.34 s
cpu-time: 15.67 s
WARNING: minor issue
"""
    log_file = tmp_path / "xtb.log"
    log_file.write_text(sample)

    parser = XTBLogParser(str(log_file))
    parsed = parser.parse_all()

    assert parsed["total_energy"] == pytest.approx(-75.123456)
    assert parsed["gradient_norm"] == pytest.approx(0.000123)
    assert parsed["homo_lumo_gap"] == pytest.approx(5.4321)
    assert parsed["homo_energy"] == pytest.approx(-10.5)
    assert parsed["lumo_energy"] == pytest.approx(-5.0)
    assert parsed["dipole_moment"] == pytest.approx(1.23)
    assert parsed["wall_time"] == pytest.approx(12.34)
    assert parsed["cpu_time"] == pytest.approx(15.67)
    assert parsed["warning_count"] == 1


def test_io_save_and_load(tmp_path: Path):
    data = {"a": 1, "b": "two"}
    out = tmp_path / "results.json"
    saved = save_results_json(data, out)
    assert saved.exists()

    loaded = load_results_json(out)
    assert loaded == data


def test_compute_file_hash(tmp_path: Path):
    f = tmp_path / "in.txt"
    f.write_bytes(b"hello world")
    h = compute_file_hash(f)
    # known sha256 for "hello world"
    assert len(h) == 64
