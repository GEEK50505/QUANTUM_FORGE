"""
xTB parsing helpers centralized in backend.core.

This module contains `XTBLogParser` which was previously in
`backend/simulation/classical_sim/xtb_parser.py`. Keeping the canonical
parser under `backend.core` helps other modules import parsing helpers
from a stable location.

AUTHOR: Quantum_Forge Team
LAST_MODIFIED: 2025-11-08
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from backend.core.logger import setup_logger


class XTBLogParser:
    """Parser for xTB output logs with comprehensive logging."""

    def __init__(self, log_file: str, logger: Optional[logging.Logger] = None):
        self.log_file = Path(log_file)
        self.logger = logger or setup_logger("xtb_parser")
        self.logger.debug(f"Initializing XTBLogParser for log file: {log_file}")
        self._raw_log = None
        self._log_lines = None

    @property
    def raw_log(self) -> str:
        if self._raw_log is None:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self._raw_log = f.read()
        return self._raw_log

    @property
    def log_lines(self) -> List[str]:
        if self._log_lines is None:
            self._log_lines = self.raw_log.splitlines()
        return self._log_lines

    def extract_total_energy(self) -> Optional[float]:
        pattern = r"TOTAL ENERGY\s+(-?\d+\.\d+)\s+Eh"
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                return float(match.group(1))
        # Backwards-compatible warning message expected by older tests
        try:
            self.logger.warning("Could not extract total energy, pattern may have changed")
        except Exception:
            pass
        return None

    def extract_gradient_norm(self) -> Optional[float]:
        pattern = r"Gradient norm\s+(-?\d+\.\d+)"
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                return float(match.group(1))
        return None

    def extract_homo_lumo_gap(self) -> Optional[float]:
        pattern = r"HOMO-LUMO gap\s+(-?\d+\.\d+)\s+eV"
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                return float(match.group(1))
        # Backwards-compatible warning message expected by older tests
        try:
            self.logger.warning("Could not extract HOMO-LUMO gap, pattern may have changed")
        except Exception:
            pass
        return None

    def extract_convergence_status(self) -> Optional[str]:
        for line in self.log_lines:
            if "GEOMETRY OPTIMIZATION CONVERGED" in line:
                return "CONVERGED"
            elif "ERROR" in line and "convergence" in line.lower():
                return "FAILED"
        return None

    def extract_timing(self) -> Dict[str, Optional[float]]:
        timing = {"wall_time": None, "cpu_time": None}
        for line in self.log_lines:
            if "wall-time" in line:
                match = re.search(r"wall-time:\s+(-?\d+\.\d+)\s+s", line)
                if match:
                    timing["wall_time"] = float(match.group(1))
            elif "cpu-time" in line:
                match = re.search(r"cpu-time:\s+(-?\d+\.\d+)\s+s", line)
                if match:
                    timing["cpu_time"] = float(match.group(1))
        return timing

    def extract_homo_lumo_energies(self) -> Tuple[Optional[float], Optional[float]]:
        homo_energy = None
        lumo_energy = None
        for line in self.log_lines:
            if "HOMO/LUMO (eV)" in line:
                match = re.search(r"HOMO/LUMO \(eV\):\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", line)
                if match:
                    homo_energy = float(match.group(1))
                    lumo_energy = float(match.group(2))
                    break
        return homo_energy, lumo_energy

    def extract_dipole_moment(self) -> Optional[float]:
        pattern = r"Total dipole moment\s+(-?\d+\.\d+)\s+Debye"
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                return float(match.group(1))
        return None

    def extract_orbital_energies_list(self) -> List[Dict[str, float]]:
        orbitals = []
        in_orbital_section = False
        for line in self.log_lines:
            if "Orbital energies (eV)" in line:
                in_orbital_section = True
                continue
            elif in_orbital_section and ("---" in line or line.strip() == ""):
                in_orbital_section = False
                continue
            elif in_orbital_section:
                match = re.search(r"^\s*(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)", line)
                if match:
                    orbitals.append({
                        "index": int(match.group(1)),
                        "energy": float(match.group(2)),
                        "occupation": float(match.group(3))
                    })
        return orbitals

    def parse_all(self) -> Dict:
        total_energy = self.extract_total_energy()
        gradient_norm = self.extract_gradient_norm()
        homo_lumo_gap = self.extract_homo_lumo_gap()
        convergence_status = self.extract_convergence_status()
        timing = self.extract_timing()
        homo_energy, lumo_energy = self.extract_homo_lumo_energies()
        dipole_moment = self.extract_dipole_moment()
        orbital_energies = self.extract_orbital_energies_list()
        warning_count = sum(1 for line in self.log_lines if "WARNING" in line)
        results = {
            "total_energy": total_energy,
            "gradient_norm": gradient_norm,
            "homo_lumo_gap": homo_lumo_gap,
            "convergence_status": convergence_status,
            "wall_time": timing.get("wall_time"),
            "cpu_time": timing.get("cpu_time"),
            "homo_energy": homo_energy,
            "lumo_energy": lumo_energy,
            "dipole_moment": dipole_moment,
            "orbital_energies": orbital_energies,
            "warning_count": warning_count,
            "line_count": len(self.log_lines)
        }
        # Backwards-compatible aliases expected by older tests/consumers
        results["timing"] = {"wall_time": results.get("wall_time"), "cpu_time": results.get("cpu_time")}
        results["homo_energy_ev"] = results.get("homo_energy")
        results["lumo_energy_ev"] = results.get("lumo_energy")
        results["fermi_level_ev"] = None
        results["dipole_moment_debye"] = results.get("dipole_moment")

        return results
