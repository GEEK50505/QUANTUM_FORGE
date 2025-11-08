"""
Execute xTB calculations with full automation and logging.
"""
import os
import re
import subprocess
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any
from backend.core.logger import setup_logger, log_execution_time
from backend.core.config import get_config
from backend.simulation.classical_sim.xtb_parser import XTBLogParser


class XTBRunner:
    """Runner for xTB calculations with full automation and logging."""
    
    def __init__(self, input_xyz: str, workdir: str = './runs', logger: Optional[logging.Logger] = None):
        """
        Initialize the xTB runner.
        
        Args:
            input_xyz: Path to input XYZ file
            workdir: Working directory for calculations
            logger: Optional logger instance
        """
        self.input_xyz = Path(input_xyz)
        self.workdir = Path(workdir)
        self.logger = logger or setup_logger("xtb_runner")
        self.config = get_config()
        
        self.logger.debug(f"Initializing XTBRunner with input: {input_xyz}")
        self.logger.debug(f"Working directory: {workdir}")
        
        # Validate input file
        if not self.validate_input_file():
            raise ValueError(f"Invalid input file: {input_xyz}")
        
        # Create working directory
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Created working directory: {self.workdir}")
        
        # Generate job ID
        self.job_id = self.generate_job_id()
        self.logger.debug(f"Generated job ID: {self.job_id}")
    
    def compute_file_hash(self, filepath: str) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            filepath: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        self.logger.debug(f"Computing hash for file: {filepath}")
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            file_hash = hash_sha256.hexdigest()
            self.logger.debug(f"Computed hash for {filepath}: {file_hash}")
            return file_hash
        except Exception as e:
            self.logger.error(f"Failed to compute hash for {filepath}: {e}")
            raise
    
    def generate_job_id(self) -> str:
        """
        Generate a unique job ID with timestamp.
        
        Returns:
            Unique job ID string
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        input_name = self.input_xyz.stem
        job_id = f"{input_name}_{timestamp}"
        self.logger.debug(f"Generated job ID: {job_id}")
        return job_id
    
    def validate_input_file(self) -> bool:
        """
        Validate the input XYZ file format.
        
        Returns:
            True if valid, False otherwise
        """
        self.logger.debug(f"Validating input file: {self.input_xyz}")
        
        if not self.input_xyz.exists():
            self.logger.error(f"Input file does not exist: {self.input_xyz}")
            return False
        
        try:
            with open(self.input_xyz, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                self.logger.error(f"Input file too short: {self.input_xyz}")
                return False
            
            # Check first line is atom count
            try:
                atom_count = int(lines[0].strip())
            except ValueError:
                self.logger.error(f"First line is not a valid atom count: {lines[0]}")
                return False
            
            # Check we have enough lines
            if len(lines) < atom_count + 2:
                self.logger.error(f"Not enough lines for {atom_count} atoms")
                return False
            
            self.logger.info(f"Input file validation passed: {atom_count} atoms found")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate input file {self.input_xyz}: {e}")
            return False
    
    def run(self, optimization_level: str = 'tight', max_retries: int = None) -> Dict:
        """
        Run xTB calculation with full automation and logging.
        
        Args:
            optimization_level: Optimization level ('tight', 'normal', 'crude')
            max_retries: Maximum number of retries (defaults to config value)
            
        Returns:
            Dictionary with results and status
        """
        if max_retries is None:
            max_retries = self.config.XTB_MAX_RETRIES
            
        self.logger.info(f"Starting xTB job {self.job_id} on {self.input_xyz.name}")
        
        # Compute input hash
        input_hash = self.compute_file_hash(str(self.input_xyz))
        
        # Prepare command
        cmd = [
            "xtb",
            str(self.input_xyz),
            "--opt", optimization_level,
            "--gbsa", "water",  # Default solvent
            "--chrg", "0",      # Default charge
            "--uhf", "0"        # Default multiplicity
        ]
        
        command_line = " ".join(cmd)
        self.logger.info(f"Command: {command_line}")
        self.logger.info(f"Timeout: {self.config.XTB_TIMEOUT} seconds, Max retries: {max_retries}")
        
        # Run job with retries
        results = {
            "job_id": self.job_id,
            "input_file": str(self.input_xyz),
            "input_hash": input_hash,
            "optimization_level": optimization_level,
            "command": command_line,
            "attempts": 0,
            "success": False,
            "error": None,
            "results": None
        }
        
        for attempt in range(1, max_retries + 2):  # +1 for initial attempt
            results["attempts"] = attempt
            
            if attempt > 1:
                self.logger.info(f"Attempt {attempt}/{max_retries + 1}")
            
            try:
                with log_execution_time(self.logger, f"xTB job {self.job_id}"):
                    # Run xTB process
                    process = subprocess.Popen(
                        cmd,
                        cwd=self.workdir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Log output in real-time
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.logger.debug(f"xtb stdout: {output.strip()}")
                    
                    # Get stderr
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        self.logger.debug(f"xtb stderr: {stderr_output.strip()}")
                    
                    # Wait for completion with timeout
                    try:
                        stdout, stderr = process.communicate(timeout=self.config.XTB_TIMEOUT)
                        return_code = process.returncode
                        
                        if return_code == 0:
                            self.logger.info(f"xTB job {self.job_id} completed successfully")
                            results["success"] = True
                            break
                        else:
                            self.logger.error(f"xTB job failed with return code {return_code}")
                            results["error"] = f"Return code {return_code}: {stderr}"
                            
                    except subprocess.TimeoutExpired:
                        self.logger.error(f"xTB job timed out after {self.config.XTB_TIMEOUT} seconds")
                        process.kill()
                        stdout, stderr = process.communicate()
                        results["error"] = "Timeout"
                        
                        if attempt < max_retries + 1:
                            self.logger.info(f"Attempt {attempt}/{max_retries + 1} failed, retrying...")
                            continue
                        else:
                            break
                            
            except Exception as e:
                self.logger.error(f"Exception during xTB execution: {e}", exc_info=True)
                results["error"] = str(e)
                
                if attempt < max_retries + 1:
                    self.logger.info(f"Attempt {attempt}/{max_retries + 1} failed, retrying...")
                    continue
                else:
                    break
        
        # Parse results if successful
        if results["success"]:
            try:
                # Look for output files
                output_log = self.workdir / "xtb.log"
                if output_log.exists():
                    parser = XTBLogParser(str(output_log), self.logger)
                    parsed_results = parser.parse_all()
                    results["results"] = parsed_results
                    
                    # Log timing information
                    wall_time = parsed_results.get("wall_time")
                    cpu_time = parsed_results.get("cpu_time")
                    if wall_time and cpu_time and wall_time > 0:
                        speedup = cpu_time / wall_time
                        self.logger.info(f"Job completed in {wall_time:.2f} seconds ({speedup:.2f}x speedup)")
                else:
                    self.logger.warning("No xtb.log file found in working directory")
                    
            except Exception as e:
                self.logger.error(f"Failed to parse results: {e}", exc_info=True)
                results["error"] = f"Parsing failed: {e}"
                results["success"] = False
        
        # Log final status
        status = "CONVERGED" if results["success"] else "FAILED"
        if results["error"] == "Timeout":
            status = "TIMEOUT"
        self.logger.info(f"Job {self.job_id} final status: {status}")
        
        return results
    
    def save_results(self, results: Dict, output_dir: str = None) -> Path:
        """
        Save results to JSON file.
        
        Args:
            results: Results dictionary
            output_dir: Output directory (defaults to config value)
            
        Returns:
            Path to saved results file
        """
        if output_dir is None:
            output_dir = self.config.OUTPUT_DIR
            
        output_path = Path(output_dir) / f"{self.job_id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Saving results to {output_path}")
        
        try:
            # Handle non-serializable types
            def default_serializer(obj):
                return str(obj)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=default_serializer)
            
            # Log file size
            file_size_kb = output_path.stat().st_size / 1024
            self.logger.info(f"Results JSON size: {file_size_kb:.1f} KB")
            
            # Log output files
            output_files = list(self.workdir.glob("*"))
            self.logger.info(f"Output files: {[f.name for f in output_files]}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save results to {output_path}: {e}", exc_info=True)
            raise
    
    def save_metadata(self, results: Dict, output_dir: str = None) -> Path:
        """
        Save metadata to JSON file.
        
        Args:
            results: Results dictionary
            output_dir: Output directory (defaults to config value)
            
        Returns:
            Path to saved metadata file
        """
        if output_dir is None:
            output_dir = self.config.OUTPUT_DIR
            
        self.logger.info(f"Generating metadata for job {self.job_id}")
        
        # Extract timing and convergence info
        parsed_results = results.get("results", {})
        metadata = {
            "job_id": self.job_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": str(self.input_xyz),
            "input_hash": results.get("input_hash", ""),
            "method": results.get("optimization_level", ""),
            "convergence_status": parsed_results.get("convergence_status", "UNKNOWN"),
            "wall_time": parsed_results.get("wall_time"),
            "cpu_time": parsed_results.get("cpu_time"),
            "total_energy": parsed_results.get("total_energy"),
            "homo_lumo_gap": parsed_results.get("homo_lumo_gap"),
            "success": results.get("success", False),
            "attempts": results.get("attempts", 0)
        }
        
        metadata_path = Path(output_dir) / f"{self.job_id}_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Metadata saved to {metadata_path}")
            return metadata_path
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata to {metadata_path}: {e}", exc_info=True)
            raise