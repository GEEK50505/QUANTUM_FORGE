"""
File: backend/core/xtb_runner.py

PURPOSE:
This module provides XTBRunner, a thin orchestration layer to execute the
extended Tight Binding (xTB) quantum chemistry binary, capture output,
parse JSON results and return a structured summary to the rest of the
application.

TECHNICAL TERMS:

xTB: extended Tight Binding — a fast semi-empirical quantum chemistry method
used for geometry optimization and electronic-structure estimations.

HOMO/LUMO: Highest Occupied / Lowest Unoccupied Molecular Orbitals.
Hartree: Atomic unit of energy (1 Hartree ≈ 27.2 eV).

DEPENDENCIES:

subprocess: run external xTB process
json: parse JSON-encoded xTB output
logging: instrument execution for observability
pathlib: filesystem helpers

AUTHOR: Quantum_Forge Team
LAST MODIFIED: 2025-11-08
"""

import subprocess
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from backend.config import XTBConfig, get_logger


class XTBRunner:
    """
    Manages execution of xTB calculations and parsing results into a stable
    dictionary returned to callers.

    WHY THIS CLASS EXISTS:
    - Centralizes the command invocation and error handling for xTB so the
      rest of the system can request calculations without duplicating safety
      checks (timeouts, validation, parsing errors).
    - Provides clear success/failure contract used by job managers and APIs.

    CONTRACT:
    - Input: path to an XYZ file and a job identifier
    - Output: dict { success: bool, energy: Optional[float], results: Optional[dict], error: Optional[str] }

    ERROR MODES:
    - Invalid input file -> success=False + explanatory message
    - xTB process error / non-zero exit -> success=False + stderr
    - JSON parse error -> success=False + parse error message
    - Timeout -> success=False + 'Timeout'
    """

    def __init__(self, config: XTBConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the runner.

        PARAMETERS:
        - config: XTBConfig with configuration values (paths, timeouts, workdir)
        - logger: optional logging.Logger instance; if omitted a module logger is used

        VALIDATION:
        - The constructor logs its initialization but does not call the binary
          at construction time to keep initialization side-effect free.
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

        # Ensure we pass an absolute path to the xTB binary to avoid
        # working-directory-relative resolution issues. This prevents
        # cases where validation (running in the API CWD) succeeds but
        # xTB (launched with a different cwd) can't find the file.
        try:
            xyz_file_path = str(Path(xyz_file_path).resolve())
        except Exception:
            # fallback: keep original
            xyz_file_path = str(xyz_file_path)
        
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

            # Prepare environment: force single-threaded for threaded native libs
            # to avoid native crashes when running from a long-lived service.
            env = os.environ.copy()
            env.setdefault("OMP_NUM_THREADS", "1")
            env.setdefault("MKL_NUM_THREADS", "1")
            env.setdefault("KMP_AFFINITY", "none")
            # Log a minimal hint about the enforced env (do not log full env)
            self.logger.debug(f"Running xTB with OMP_NUM_THREADS={env.get('OMP_NUM_THREADS')} MKL_NUM_THREADS={env.get('MKL_NUM_THREADS')}")


            # Ensure per-job directory exists and run xTB with that as cwd.
            # Running in the job-specific directory avoids permission/relative-path
            # issues where xTB attempts to write files into a shared WORKDIR.
            job_dir = Path(self.config.JOBS_DIR) / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            # Run xTB inside the job directory so all output files are colocated
            result = subprocess.run(
                cmd,
                cwd=str(job_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.XTB_TIMEOUT
            )

            # Persist raw stdout/stderr to the job directory for debugging
            try:
                (job_dir / "xtb_stdout.log").write_text(result.stdout or "")
                (job_dir / "xtb_stderr.log").write_text(result.stderr or "")
            except Exception:
                # Don't fail the run if we can't write logs; just continue
                self.logger.debug(f"Could not write xtb logs for job {job_id}", exc_info=True)

            self.logger.info(f"xTB completed for {job_id} with return code {result.returncode}")
            
            # Parse output
            if result.returncode == 0:
                # First try: parse stdout directly (works with the mock xtb that
                # prints JSON to stdout). If that fails, fall back to looking for
                # an `xtbout.json` file that the real xTB often writes in the
                # working directory (or its run subdirectory). If we still can't
                # find JSON, attempt a last-ditch extraction of a JSON object
                # from stdout.
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
                except json.JSONDecodeError as e_stdout:
                    self.logger.debug(f"Stdout JSON parse failed for {job_id}: {e_stdout}")
                    # Attempt to locate xtbout.json under WORKDIR
                    try:
                        workdir = Path(self.config.WORKDIR)
                        candidates = list(workdir.rglob('xtbout.json'))
                        self.logger.debug(f"Found {len(candidates)} xtbout.json candidates under {workdir}")
                        chosen = None
                        for cand in candidates:
                            try:
                                with open(cand, 'r') as fh:
                                    cand_data = json.load(fh)
                                # prefer a candidate that references our job xyz path
                                prog_call = cand_data.get('program call') or cand_data.get('program_call') or ''
                                if xyz_file_path in prog_call or job_id in str(cand):
                                    chosen = cand_data
                                    break
                                # otherwise keep the first parseable as fallback
                                if chosen is None:
                                    chosen = cand_data
                            except Exception:
                                continue

                        if chosen is not None:
                            parsed_results = self.parse_xtb_output(chosen)
                            self.logger.info(f"Parsed results from xtbout.json for {job_id} - Energy: {parsed_results.get('energy')}")
                            return {
                                "success": True,
                                "energy": parsed_results.get("energy"),
                                "results": parsed_results,
                                "error": None
                            }
                    except Exception:
                        self.logger.debug(f"Failed to locate/parse xtbout.json for {job_id}", exc_info=True)

                    # Last attempt: try to extract a JSON object from stdout
                    try:
                        s = result.stdout or ""
                        first = s.find('{')
                        last = s.rfind('}')
                        if first != -1 and last != -1 and last > first:
                            candidate = s[first:last+1]
                            parsed_results = self.parse_xtb_output(candidate)
                            self.logger.info(f"Parsed JSON object extracted from stdout for {job_id} - Energy: {parsed_results.get('energy')}")
                            return {
                                "success": True,
                                "energy": parsed_results.get("energy"),
                                "results": parsed_results,
                                "error": None
                            }
                    except Exception:
                        self.logger.debug(f"Failed to extract JSON from stdout for {job_id}", exc_info=True)

                    # Final fallback: try to extract a numeric energy from stdout
                    try:
                        import re
                        s = result.stdout or ""
                        # Common xtb summary lines contain labels like 'SCC energy' or 'total energy'
                        # Try several patterns and prefer SCC/electronic energy when available.
                        patterns = [
                            r"SCC energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)",
                            r"SCC energy\s*([-+]?[0-9]*\.?[0-9]+)\s*Eh",
                            r"electronic energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)",
                            r"total energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)\s*Eh",
                            r"total energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)"
                        ]
                        found = None
                        for p in patterns:
                            m = re.search(p, s, re.IGNORECASE)
                            if m:
                                try:
                                    found = float(m.group(1))
                                    break
                                except Exception:
                                    continue

                        if found is not None:
                            parsed_results = {"energy": found}
                            self.logger.info(f"Extracted energy via stdout regex for {job_id}: {found}")
                            return {
                                "success": True,
                                "energy": found,
                                "results": parsed_results,
                                "error": None
                            }
                    except Exception:
                        self.logger.debug(f"Failed regex energy extraction for {job_id}", exc_info=True)

                    # If we get here, we could not parse JSON by any fallback
                    self.logger.error(f"Failed to parse JSON output for {job_id}: {e_stdout}")
                    return {
                        "success": False,
                        "energy": None,
                        "results": None,
                        "error": f"Failed to parse JSON output: {e_stdout}"
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
            # Accept either a JSON string or an already-loaded dict.
            if isinstance(json_output, dict):
                data = json_output
            else:
                data = json.loads(json_output)

            # Build a normalized key lookup to tolerate spacing/case/punctuation
            # differences between xTB releases and wrapper scripts.
            import re
            normalized: Dict[str, str] = {}
            for k in data.keys():
                nk = re.sub(r'[^a-z0-9]', '', k.lower())
                normalized[nk] = k

            self.logger.debug(f"Parsing xTB output with keys: {list(data.keys())}")
            results = {}

            # Check normalized keys in priority order: electronic energy -> total energy -> energy
            chosen_key = None
            for nk in ('electronicenergy', 'totalenergy', 'energy'):
                if nk in normalized:
                    chosen_key = normalized[nk]
                    break

            def _to_float_maybe(x):
                try:
                    if x is None:
                        return None
                    return float(x)
                except Exception:
                    return None

            if chosen_key is not None:
                val = data.get(chosen_key)
                f = _to_float_maybe(val)
                results['energy'] = f if f is not None else val
                self.logger.debug(f"Selected energy key '{chosen_key}' -> {results.get('energy')}")

            # Gradient norm (normalized forms)
            for nk in ('gradientnorm', 'gradientnorm'):
                if nk in normalized:
                    key = normalized[nk]
                    gv = _to_float_maybe(data.get(key))
                    results['gradient_norm'] = gv if gv is not None else data.get(key)
                    break

            # HOMO / LUMO / gap (normalized lookup)
            if 'homo' in normalized:
                results['homo'] = data.get(normalized['homo'])
            if 'lumo' in normalized:
                results['lumo'] = data.get(normalized['lumo'])
            for nk in ('homolumogap', 'homolumogapev', 'homolumo', 'homolumogap'):
                if nk in normalized:
                    key = normalized[nk]
                    gv = _to_float_maybe(data.get(key))
                    results['homo_lumo_gap'] = gv if gv is not None else data.get(key)
                    break

            # Dipole and charges (normalized)
            for nk in ('dipole', 'dipoleau', 'dipoleau'):
                if nk in normalized:
                    results['dipole'] = data.get(normalized[nk])
                    break
            for nk in ('partialcharges', 'charges'):
                if nk in normalized:
                    results['charges'] = data.get(normalized[nk])
                    break

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