"""
Execute xTB calculations with full error handling and logging.
"""
import subprocess
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional
from backend.config import XTBConfig, get_logger


class XTBRunner:
    """Execute xTB calculations with full error handling and logging."""
    
    def __init__(self, config: XTBConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the XTB runner.
        
        Args:
            config: XTBConfig instance
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or get_logger(__name__)
        self.logger.info("Initializing XTBRunner")
    
    def execute(self, xyz_file_path: str, job_id: str, optimization_level: str = "normal") -> Dict:
        """
        Execute xTB calculation.
        
        Args:
            xyz_file_path: Path to XYZ file
            job_id: Job identifier
            optimization_level: Optimization level ("normal", "tight", "crude")
            
        Returns:
            Dictionary with results
        """
        self.logger.info(f"Starting xTB for {job_id}")
        
        try:
            # Validate input
            if not self.validate_input(xyz_file_path):
                return {
                    "success": False,
                    "energy": None,
                    "results": None,
                    "error": "Invalid XYZ file"
                }
            
            # Prepare command
            cmd = [
                self.config.XTB_EXECUTABLE,
                xyz_file_path,
                "--opt", optimization_level,
                "--json"
            ]
            
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Run xTB
            result = subprocess.run(
                cmd,
                cwd=self.config.WORKDIR,
                capture_output=True,
                text=True,
                timeout=self.config.XTB_TIMEOUT
            )
            
            self.logger.info(f"xTB completed for {job_id} with return code {result.returncode}")
            
            # Parse output
            if result.returncode == 0:
                try:
                    json_output = result.stdout
                    parsed_results = self.parse_xtb_output(json_output)
                    self.logger.info(f"xTB completed {job_id} - Energy: {parsed_results.get('energy')}")
                    return {
                        "success": True,
                        "energy": parsed_results.get("energy"),
                        "results": parsed_results,
                        "error": None
                    }
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON output for {job_id}: {e}")
                    return {
                        "success": False,
                        "energy": None,
                        "results": None,
                        "error": f"Failed to parse JSON output: {e}"
                    }
            else:
                self.logger.error(f"xTB failed for {job_id}: {result.stderr}")
                return {
                    "success": False,
                    "energy": None,
                    "results": None,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"xTB timed out for {job_id} after {self.config.XTB_TIMEOUT} seconds")
            return {
                "success": False,
                "energy": None,
                "results": None,
                "error": "Timeout"
            }
        except Exception as e:
            self.logger.error(f"xTB execution failed for {job_id}: {e}", exc_info=True)
            return {
                "success": False,
                "energy": None,
                "results": None,
                "error": str(e)
            }
    
    def parse_xtb_output(self, json_output: str) -> Dict:
        """
        Parse xTB JSON output.
        
        Args:
            json_output: JSON output string
            
        Returns:
            Dictionary with parsed results
        """
        try:
            data = json.loads(json_output)
            self.logger.debug(f"Parsing xTB output with keys: {list(data.keys())}")
            
            # Extract key values
            results = {}
            
            # Total energy
            if "total_energy" in data:
                results["energy"] = data["total_energy"]
            elif "energy" in data:
                results["energy"] = data["energy"]
            
            # Gradient norm
            if "gradient_norm" in data:
                results["gradient_norm"] = data["gradient_norm"]
            
            # HOMO and LUMO
            if "homo" in data:
                results["homo"] = data["homo"]
            if "lumo" in data:
                results["lumo"] = data["lumo"]
            if "homo_lumo_gap" in data:
                results["homo_lumo_gap"] = data["homo_lumo_gap"]
            
            # Dipole moment
            if "dipole" in data:
                results["dipole"] = data["dipole"]
            
            # Atomic charges
            if "charges" in data:
                results["charges"] = data["charges"]
            
            self.logger.info(f"Parsed results: energy={results.get('energy')}, "
                           f"gap={results.get('homo_lumo_gap')}, "
                           f"gradient={results.get('gradient_norm')}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse xTB output: {e}", exc_info=True)
            raise
    
    def validate_input(self, xyz_file_path: str) -> bool:
        """
        Validate XYZ file input.
        
        Args:
            xyz_file_path: Path to XYZ file
            
        Returns:
            True if valid, False otherwise
        """
        self.logger.debug(f"Validating input file: {xyz_file_path}")
        
        try:
            xyz_path = Path(xyz_file_path)
            
            # Check file exists
            if not xyz_path.exists():
                self.logger.error(f"XYZ file does not exist: {xyz_file_path}")
                return False
            
            # Check file is readable
            if not xyz_path.is_file():
                self.logger.error(f"XYZ path is not a file: {xyz_file_path}")
                return False
            
            # Read and validate XYZ format
            with open(xyz_path, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                self.logger.error(f"XYZ file too short: {xyz_file_path}")
                return False
            
            # First line should be number of atoms
            try:
                atom_count = int(lines[0].strip())
            except ValueError:
                self.logger.error(f"First line is not a valid atom count: {lines[0]}")
                return False
            
            # Check we have enough lines for atoms
            if len(lines) < atom_count + 2:
                self.logger.error(f"Not enough lines for {atom_count} atoms in {xyz_file_path}")
                return False
            
            self.logger.info(f"XYZ file validation passed: {atom_count} atoms found")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate XYZ file {xyz_file_path}: {e}", exc_info=True)
            return False