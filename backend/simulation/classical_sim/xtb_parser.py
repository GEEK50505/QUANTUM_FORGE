"""
Parse xTB output logs with comprehensive logging.
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from backend.core.logger import setup_logger


class XTBLogParser:
    """Parser for xTB output logs with comprehensive logging."""
    
    def __init__(self, log_file: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the xTB log parser.
        
        Args:
            log_file: Path to the xTB output log file
            logger: Optional logger instance
        """
        self.log_file = Path(log_file)
        self.logger = logger or setup_logger("xtb_parser")
        self.logger.debug(f"Initializing XTBLogParser for log file: {log_file}")
        
        # Cache for raw log content
        self._raw_log = None
        self._log_lines = None
    
    @property
    def raw_log(self) -> str:
        """Get raw log content, cached to avoid re-reading."""
        if self._raw_log is None:
            self.logger.debug(f"Reading log file: {self.log_file}")
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self._raw_log = f.read()
                self.logger.debug(f"Successfully read {len(self._raw_log)} characters from log file")
            except Exception as e:
                self.logger.error(f"Failed to read log file {self.log_file}: {e}")
                raise
        return self._raw_log
    
    @property
    def log_lines(self) -> List[str]:
        """Get log lines as a list, cached to avoid re-processing."""
        if self._log_lines is None:
            self._log_lines = self.raw_log.splitlines()
            self.logger.debug(f"Log contains {len(self._log_lines)} lines")
        return self._log_lines
    
    def extract_total_energy(self) -> Optional[float]:
        """
        Extract total energy from xTB log.
        
        Returns:
            Total energy in Hartree or None if not found
        """
        self.logger.debug("Extracting total energy")
        pattern = r"TOTAL ENERGY\s+(-?\d+\.\d+)\s+Eh"
        
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                energy = float(match.group(1))
                self.logger.debug(f"Extracted total_energy: {energy} Hartree")
                return energy
        
        self.logger.warning("Could not extract total energy, pattern may have changed")
        return None
    
    def extract_gradient_norm(self) -> Optional[float]:
        """
        Extract gradient norm from xTB log.
        
        Returns:
            Gradient norm or None if not found
        """
        self.logger.debug("Extracting gradient norm")
        pattern = r"Gradient norm\s+(-?\d+\.\d+)"
        
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                gradient = float(match.group(1))
                self.logger.debug(f"Extracted gradient_norm: {gradient}")
                return gradient
        
        self.logger.warning("Could not extract gradient norm, pattern may have changed")
        return None
    
    def extract_homo_lumo_gap(self) -> Optional[float]:
        """
        Extract HOMO-LUMO gap from xTB log.
        
        Returns:
            HOMO-LUMO gap in eV or None if not found
        """
        self.logger.debug("Extracting HOMO-LUMO gap")
        pattern = r"HOMO-LUMO gap\s+(-?\d+\.\d+)\s+eV"
        
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                gap = float(match.group(1))
                self.logger.debug(f"Extracted homo_lumo_gap: {gap} eV")
                return gap
        
        self.logger.warning("Could not extract HOMO-LUMO gap, pattern may have changed")
        return None
    
    def extract_convergence_status(self) -> Optional[str]:
        """
        Extract convergence status from xTB log.
        
        Returns:
            Convergence status string or None if not found
        """
        self.logger.debug("Extracting convergence status")
        
        # Check for convergence messages
        for line in self.log_lines:
            if "GEOMETRY OPTIMIZATION CONVERGED" in line:
                self.logger.debug("Extracted convergence_status: CONVERGED")
                return "CONVERGED"
            elif "ERROR" in line and "convergence" in line.lower():
                self.logger.debug("Extracted convergence_status: FAILED")
                return "FAILED"
        
        self.logger.warning("Could not determine convergence status")
        return None
    
    def extract_timing(self) -> Dict[str, Optional[float]]:
        """
        Extract timing information from xTB log.
        
        Returns:
            Dictionary with wall_time and cpu_time
        """
        self.logger.debug("Extracting timing information")
        timing = {"wall_time": None, "cpu_time": None}
        
        # Look for timing information
        for line in self.log_lines:
            if "wall-time" in line:
                match = re.search(r"wall-time:\s+(-?\d+\.\d+)\s+s", line)
                if match:
                    timing["wall_time"] = float(match.group(1))
                    self.logger.debug(f"Extracted wall_time: {timing['wall_time']} seconds")
            elif "cpu-time" in line:
                match = re.search(r"cpu-time:\s+(-?\d+\.\d+)\s+s", line)
                if match:
                    timing["cpu_time"] = float(match.group(1))
                    self.logger.debug(f"Extracted cpu_time: {timing['cpu_time']} seconds")
        
        if timing["wall_time"] is None and timing["cpu_time"] is None:
            self.logger.warning("Could not extract timing information")
        
        return timing
    
    def extract_homo_lumo_energies(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract HOMO and LUMO energies from xTB log.
        
        Returns:
            Tuple of (HOMO energy, LUMO energy) in eV or None if not found
        """
        self.logger.debug("Extracting HOMO and LUMO energies")
        homo_energy = None
        lumo_energy = None
        
        # Look for orbital energies section
        for line in self.log_lines:
            if "HOMO/LUMO (eV)" in line:
                match = re.search(r"HOMO/LUMO \(eV\):\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", line)
                if match:
                    homo_energy = float(match.group(1))
                    lumo_energy = float(match.group(2))
                    self.logger.debug(f"Extracted HOMO: {homo_energy} eV, LUMO: {lumo_energy} eV")
                    break
        
        if homo_energy is None or lumo_energy is None:
            self.logger.warning("Could not extract HOMO/LUMO energies, pattern may have changed")
        
        return homo_energy, lumo_energy
    
    def extract_dipole_moment(self) -> Optional[float]:
        """
        Extract dipole moment from xTB log.
        
        Returns:
            Dipole moment in Debye or None if not found
        """
        self.logger.debug("Extracting dipole moment")
        pattern = r"Total dipole moment\s+(-?\d+\.\d+)\s+Debye"
        
        for line in self.log_lines:
            match = re.search(pattern, line)
            if match:
                dipole = float(match.group(1))
                self.logger.debug(f"Extracted dipole_moment: {dipole} Debye")
                return dipole
        
        self.logger.warning("Could not extract dipole moment, pattern may have changed")
        return None
    
    def extract_orbital_energies_list(self) -> List[Dict[str, float]]:
        """
        Extract list of orbital energies from xTB log.
        
        Returns:
            List of dictionaries with orbital information
        """
        self.logger.debug("Extracting orbital energies list")
        orbitals = []
        
        # Look for orbital energies section
        in_orbital_section = False
        for line in self.log_lines:
            if "Orbital energies (eV)" in line:
                in_orbital_section = True
                continue
            elif in_orbital_section and ("---" in line or line.strip() == ""):
                in_orbital_section = False
                continue
            elif in_orbital_section:
                # Parse orbital line: "1   -10.5423   2.0000"
                match = re.search(r"^\s*(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)", line)
                if match:
                    orbital = {
                        "index": int(match.group(1)),
                        "energy": float(match.group(2)),
                        "occupation": float(match.group(3))
                    }
                    orbitals.append(orbital)
        
        self.logger.debug(f"Extracted {len(orbitals)} orbital energies")
        return orbitals
    
    def parse_all(self) -> Dict:
        """
        Parse all available information from xTB log.
        
        Returns:
            Dictionary with all extracted values
        """
        self.logger.info("Parsing xTB output log")
        
        try:
            # Extract all values
            total_energy = self.extract_total_energy()
            gradient_norm = self.extract_gradient_norm()
            homo_lumo_gap = self.extract_homo_lumo_gap()
            convergence_status = self.extract_convergence_status()
            timing = self.extract_timing()
            homo_energy, lumo_energy = self.extract_homo_lumo_energies()
            dipole_moment = self.extract_dipole_moment()
            orbital_energies = self.extract_orbital_energies_list()
            
            # Count warnings
            warning_count = sum(1 for line in self.log_lines if "WARNING" in line)
            
            # Create results dictionary
            results = {
                "total_energy": total_energy,
                "gradient_norm": gradient_norm,
                "homo_lumo_gap": homo_lumo_gap,
                "convergence_status": convergence_status,
                "wall_time": timing["wall_time"],
                "cpu_time": timing["cpu_time"],
                "homo_energy": homo_energy,
                "lumo_energy": lumo_energy,
                "dipole_moment": dipole_moment,
                "orbital_energies": orbital_energies,
                "warning_count": warning_count,
                "line_count": len(self.log_lines)
            }
            
            # Log statistics
            extracted_count = sum(1 for v in results.values() 
                                if v is not None and (not isinstance(v, list) or len(v) > 0))
            self.logger.info(f"Parsed log with {len(self.log_lines)} lines, "
                           f"extracted {extracted_count} properties, {warning_count} warnings")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse log file {self.log_file}: {e}", exc_info=True)
            raise