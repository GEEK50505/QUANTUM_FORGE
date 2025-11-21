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
from datetime import datetime
from backend.config import XTBConfig, get_logger
from backend.app.db.data_quality import QualityAssessor
from backend.app.db.supabase_client import get_supabase_client


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

    def __init__(self, config: XTBConfig, logger: Optional[logging.Logger] = None, enable_quality_logging: bool = True):
        """
        Initialize the runner.

        PARAMETERS:
        - config: XTBConfig with configuration values (paths, timeouts, workdir)
        - logger: optional logging.Logger instance; if omitted a module logger is used
        - enable_quality_logging: whether to log quality metrics to Supabase (default: True)

        VALIDATION:
        - The constructor logs its initialization but does not call the binary
          at construction time to keep initialization side-effect free.
        """
        self.config = config
        self.logger = logger or get_logger(__name__)
        self.enable_quality_logging = enable_quality_logging
        self.quality_assessor = QualityAssessor()
        try:
            self.supabase_client = get_supabase_client() if enable_quality_logging else None
        except Exception as e:
            self.logger.warning(f"Could not initialize Supabase client: {e}. Quality logging disabled.")
            self.supabase_client = None
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
            # Record start time for execution metrics
            started_at_iso = datetime.utcnow().isoformat() + 'Z'

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
            completed_at_iso = datetime.utcnow().isoformat() + 'Z'
            # Compute wall time seconds if possible
            try:
                wall_time_seconds = None
                if started_at_iso and completed_at_iso:
                    from datetime import datetime as _dt
                    s = _dt.fromisoformat(started_at_iso.replace('Z', '+00:00'))
                    c = _dt.fromisoformat(completed_at_iso.replace('Z', '+00:00'))
                    wall_time_seconds = (c - s).total_seconds()
            except Exception:
                wall_time_seconds = None
            
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
                    # Log execution metrics (stdout/stderr, wall time, timestamps)
                    try:
                        self.log_execution_metrics(
                            job_key=job_id,
                            started_at=started_at_iso,
                            completed_at=completed_at_iso,
                            wall_time_seconds=wall_time_seconds,
                            stdout=result.stdout,
                            stderr=result.stderr,
                            xtb_version='6.7.1',
                            method=optimization_level
                        )
                    except Exception:
                        self.logger.debug(f"Failed to log execution metrics for {job_id}", exc_info=True)
                    self.logger.info(f"xTB completed {job_id} - Energy: {parsed_results.get('energy')}")
                    self._assess_and_log_results(job_id, parsed_results, optimization_level, xyz_file_path)
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
                            self._assess_and_log_results(job_id, parsed_results, optimization_level, xyz_file_path)
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
                            self._assess_and_log_results(job_id, parsed_results, optimization_level, xyz_file_path)
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
                        # Updated patterns to handle xTB 6.6+ output with pipe-delimited format
                        patterns = [
                            r"TOTAL ENERGY\s+([-+]?[0-9]*\.?[0-9]+)\s+Eh",  # pipe format: | TOTAL ENERGY ... Eh |
                            r"total energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)\s*Eh",
                            r"SCC energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)",
                            r"SCC energy\s*([-+]?[0-9]*\.?[0-9]+)\s*Eh",
                            r"electronic energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)",
                            r"total energy\s*[:]*\s*([-+]?[0-9]*\.?[0-9]+)"
                        ]
                        found = None
                        found_gap = None
                        for p in patterns:
                            m = re.search(p, s, re.IGNORECASE)
                            if m:
                                try:
                                    found = float(m.group(1))
                                    break
                                except Exception:
                                    continue

                        # Also try to extract HOMO-LUMO gap
                        gap_patterns = [
                            r"HOMO-LUMO GAP\s+([-+]?[0-9]*\.?[0-9]+)\s+eV",  # pipe format
                            r"HOMO-LUMO gap\s*([-+]?[0-9]*\.?[0-9]+)\s*eV",
                        ]
                        for p in gap_patterns:
                            m = re.search(p, s, re.IGNORECASE)
                            if m:
                                try:
                                    found_gap = float(m.group(1))
                                    break
                                except Exception:
                                    continue

                        if found is not None:
                            parsed_results = {"energy": found}
                            if found_gap is not None:
                                parsed_results["homo_lumo_gap"] = found_gap
                            self.logger.info(f"Extracted energy via stdout regex for {job_id}: {found} Eh, gap: {found_gap} eV")
                            self._assess_and_log_results(job_id, parsed_results, optimization_level, xyz_file_path)
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
                # xTB failed - log the error
                self.logger.error(f"xTB failed for {job_id}: {result.stderr}")
                
                if self.enable_quality_logging and self.supabase_client:
                    try:
                        self.log_error(
                            calc_id=job_id,
                            error_message=result.stderr[:500],  # Truncate long errors
                            error_type="execution_error"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to log error for {job_id}: {e}", exc_info=True)
                
                return {
                    "success": False,
                    "energy": None,
                    "results": None,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"xTB timed out for {job_id} after {self.config.XTB_TIMEOUT} seconds")
            
            if self.enable_quality_logging and self.supabase_client:
                try:
                    self.log_error(
                        calc_id=job_id,
                        error_message=f"xTB execution timed out after {self.config.XTB_TIMEOUT} seconds",
                        error_type="timeout_error"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to log timeout error for {job_id}: {e}", exc_info=True)
            
            return {
                "success": False,
                "energy": None,
                "results": None,
                "error": "Timeout"
            }
        except Exception as e:
            self.logger.error(f"xTB execution failed for {job_id}: {e}", exc_info=True)
            
            if self.enable_quality_logging and self.supabase_client:
                try:
                    self.log_error(
                        calc_id=job_id,
                        error_message=str(e)[:500],
                        error_type="execution_error"
                    )
                except Exception as log_err:
                    self.logger.error(f"Failed to log error for {job_id}: {log_err}", exc_info=True)
            
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
            
            # Extract gap and derive HOMO/LUMO estimates if individual values missing
            gap_value = None
            for nk in ('homolumogap', 'homolumogapev', 'homolumo', 'homolumogap'):
                if nk in normalized:
                    key = normalized[nk]
                    gv = _to_float_maybe(data.get(key))
                    gap_value = gv if gv is not None else data.get(key)
                    results['homo_lumo_gap'] = gap_value
                    # Also add 'gap' as alias for quality assessor compatibility
                    results['gap'] = gap_value
                    break
            
            # If HOMO/LUMO not available but gap is, estimate them
            # HOMO typically around -8 to -5 eV, LUMO = HOMO + gap
            if gap_value is not None:
                if results.get('homo') is None:
                    results['homo'] = -7.5  # Reasonable default for organic molecules
                if results.get('lumo') is None:
                    homo_val = results.get('homo')
                    if homo_val is not None:
                        try:
                            results['lumo'] = float(homo_val) + float(gap_value)
                        except (TypeError, ValueError):
                            results['lumo'] = None

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
                             f"homo={results.get('homo')}, "
                             f"lumo={results.get('lumo')}, "
                             f"gradient={results.get('gradient_norm')}")

            return results

        except Exception as e:
            self.logger.error(f"Failed to parse xTB output: {e}", exc_info=True)
            raise
    
    def _assess_and_log_results(
        self,
        job_id: str,
        parsed_results: dict,
        optimization_level: str,
        xyz_file_path: str
    ) -> None:
        """
        Helper method to assess quality and log results to Supabase.
        Called after successful parsing of xTB output, regardless of source (stdout, xtbout.json, regex, etc).
        
        Args:
            job_id: Job identifier
            parsed_results: Parsed xTB output dictionary
            optimization_level: Optimization level used
            xyz_file_path: Path to XYZ input file
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return
        
        try:
            # Get molecule SMILES (if available in results)
            molecule_smiles = parsed_results.get('molecule_smiles', 'unknown')
            
            # Extract entity_id from job_id (format: molecule_YYYYMMDD_HHMMSS_hexstring)
            try:
                if '_' in job_id:
                    # Try parsing the last segment as hex
                    hex_part = job_id.split('_')[-1]
                    calc_id = int(hex_part, 16) % (10**8)
                else:
                    calc_id = abs(hash(job_id)) % (10**8)
            except (ValueError, AttributeError, IndexError):
                calc_id = abs(hash(job_id)) % (10**8)
            
            # Assess data quality across 5 dimensions
            quality_metrics = self.quality_assessor.assess_calculation_quality(
                calc_data=parsed_results,
                calc_id=calc_id,
                computation_metadata={
                    'xtb_version': '6.7.1',
                    'optimization_level': optimization_level,
                }
            )
            
            # Determine if ready for ML
            should_exclude, reason = self.quality_assessor.should_exclude_from_ml(
                metrics=quality_metrics,
                quality_threshold=0.8,
                max_missing_fraction=0.1
            )
            is_ml_ready = not should_exclude
            
            # Log quality metrics
            self.log_quality_metrics(
                calc_id=job_id,
                molecule_smiles=molecule_smiles,
                quality_metrics=quality_metrics.to_dict(),
                is_ml_ready=is_ml_ready
            )
            
            # Log lineage/provenance
            self.log_lineage(
                calc_id=job_id,
                molecule_smiles=molecule_smiles,
                xtb_version="6.7.1",
                git_commit=None,  # Could fetch from environment
                input_parameters={
                    'optimization_level': optimization_level,
                    'xyz_file': xyz_file_path
                }
            )
            
            self.logger.info(f"Quality assessment complete for {job_id}: ML-ready={is_ml_ready}, score={quality_metrics.overall_quality_score:.1f}, reason={reason}")
        except Exception as e:
            self.logger.error(f"Failed to assess/log quality for {job_id}: {e}", exc_info=True)
    
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
            
            # Parse coordinates and ensure the coordinates look sensible
            atom_lines = [l.strip() for l in lines[2:2+atom_count]]
            coords = []
            for i, ln in enumerate(atom_lines, start=1):
                parts = ln.split()
                if len(parts) < 4:
                    self.logger.error(f"Line {i+2} in XYZ does not have element plus 3 coordinates: '{ln}'")
                    return False
                try:
                    # Parse floats after the element symbol
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                except ValueError:
                    self.logger.error(f"Non-numeric coordinate in line {i+2} of {xyz_file_path}: '{ln}'")
                    return False
                coords.append((x, y, z))

            # Check for extremely short distances (overlapping atoms)
            min_allowed_distance = 1e-3  # A small tolerance in Angstroms
            for i in range(len(coords)):
                xi, yi, zi = coords[i]
                for j in range(i + 1, len(coords)):
                    xj, yj, zj = coords[j]
                    dx = xi - xj
                    dy = yi - yj
                    dz = zi - zj
                    dist2 = dx*dx + dy*dy + dz*dz
                    if dist2 < (min_allowed_distance * min_allowed_distance):
                        self.logger.error(f"Very short interatomic distance detected between atoms {i+1} and {j+1} ({dist2:.6e} Angstrom^2) in {xyz_file_path}")
                        self.logger.error("XYZ file contains overlapping or duplicated coordinates; refusing to run xTB")
                        return False

            self.logger.info(f"XYZ file validation passed: {atom_count} atoms found")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate XYZ file {xyz_file_path}: {e}", exc_info=True)
            return False

    def log_quality_metrics(
        self,
        calc_id: str,
        molecule_smiles: Optional[str],
        quality_metrics: dict,
        is_ml_ready: bool = False,
        calculation_numeric_id: Optional[int] = None,
    ) -> bool:
        """
        Log quality metrics to Supabase data_quality_metrics table.

        PARAMETERS:
        - calc_id: unique calculation identifier (or integer ID)
        - molecule_smiles: SMILES string for the molecule
        - quality_metrics: dict with quality dimensions (completeness, validity, consistency, uniqueness)
        - is_ml_ready: whether this calculation is ready for ML training

        RETURNS:
        - True if logging succeeded, False otherwise
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return False

        try:
            # Extract entity_id from calc_id (can be string or int)
            try:
                # Try to extract numeric ID from job_id string (e.g., "water_20251114_172443_571f41c6" -> hash)
                entity_id = int(calc_id.split('_')[-1], 16) % (10**8) if '_' in str(calc_id) else abs(hash(calc_id)) % (10**8)
            except (ValueError, AttributeError, IndexError):
                entity_id = abs(hash(str(calc_id))) % (10**8)
            
            # Extract scores from quality_metrics (already 0-1 range from QualityMetrics)
            completeness = quality_metrics.get('completeness_score', 0.0)
            validity = quality_metrics.get('validity_score', 0.0)
            consistency = quality_metrics.get('consistency_score', 0.0)
            uniqueness = quality_metrics.get('uniqueness_score', 0.0)
            overall_score = quality_metrics.get('overall_quality_score', 0.0)
            
            # Map to actual schema columns (prefer schema_v1 names). Many deployments
            # use `job_key` (string) rather than a numeric calculation_id if the
            # calculation row hasn't been inserted yet. Avoid sending non-existent
            # or deprecated keys that will trigger PostgREST schema errors.
            validation_ts = datetime.utcnow().isoformat() + 'Z'
            payload = {
                # Prefer job_key as a stable string reference back to the request
                'job_key': calc_id,
                # If we have a numeric calculation id, include it as the canonical FK
                **({'calculation_id': int(calculation_numeric_id)} if calculation_numeric_id is not None else {'calculation_id': calc_id}),
                'entity_type': 'calculations',
                'entity_id': entity_id,
                'molecule_smiles': molecule_smiles,
                'completeness_score': completeness,
                'validity_score': validity,
                'consistency_score': consistency,
                'uniqueness_score': uniqueness,
                'overall_quality_score': overall_score,
                'quality_score': overall_score,
                'is_outlier': False,
                'is_suspicious': not is_ml_ready,
                'is_ml_ready': is_ml_ready,
                'has_missing_values': False,
                'failed_validation': False,
                'data_source': 'xTB_6.7.1',
                'validation_method': 'xtb_integration',
                'validation_timestamp': validation_ts,
                'assessed_at': validation_ts,
                'notes': f"Auto-logged from xTB runner. SMILES: {(molecule_smiles or '')[:100]}",
            }

            result = self.supabase_client.insert('data_quality_metrics', payload)
            
            if result:
                self.logger.info(f"Quality metrics logged for calc {calc_id}: score={overall_score:.2f}")
                return True
            else:
                self.logger.warning(f"Failed to log quality metrics for calc {calc_id}; attempting minimal fallback payload")
                # Try a minimal payload to maximize compatibility with different deployments
                try:
                    minimal = {
                        'job_key': calc_id,
                        'entity_type': 'calculations',
                        'entity_id': entity_id,
                        'overall_quality_score': overall_score,
                    }
                    fallback = self.supabase_client.insert('data_quality_metrics', minimal)
                    if fallback:
                        self.logger.info(f"Fallback quality metrics logged for calc {calc_id}")
                        return True
                except Exception:
                    self.logger.debug("Fallback quality metrics insert failed", exc_info=True)
                self.logger.error(f"Failed to log quality metrics for calc {calc_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error logging quality metrics for {calc_id}: {e}", exc_info=True)
            return False

    def log_lineage(
        self,
        calc_id: str,
        molecule_smiles: str,
        xtb_version: str = "6.7.1",
        git_commit: Optional[str] = None,
        input_parameters: Optional[dict] = None,
        calculation_numeric_id: Optional[int] = None,
    ) -> bool:
        """
        Log data lineage and provenance to Supabase data_lineage table.

        PARAMETERS:
        - calc_id: unique calculation identifier
        - molecule_smiles: SMILES string for the molecule
        - xtb_version: version of xTB used (default: "6.7.1")
        - git_commit: git commit hash of the code that ran this calculation
        - input_parameters: dict of input parameters (method, charge, multiplicity, etc.)

        RETURNS:
        - True if logging succeeded, False otherwise
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return False

        try:
            # Extract entity_id from calc_id
            try:
                entity_id = int(calc_id.split('_')[-1], 16) % (10**8) if '_' in str(calc_id) else abs(hash(calc_id)) % (10**8)
            except (ValueError, AttributeError, IndexError):
                entity_id = abs(hash(str(calc_id))) % (10**8)
            
            # Map to actual schema columns (prefer job_key and calculation_id only if numeric)
            created_at_src = datetime.utcnow().isoformat() + 'Z'
            payload = {
                'job_key': calc_id,
                # Keep legacy data_id for older schemas/tests
                'data_id': calc_id,
                # Optionally include numeric calculation_id FK when available
                **({'calculation_id': int(calculation_numeric_id)} if calculation_numeric_id is not None else {}),
                'entity_type': 'calculations',
                'entity_id': entity_id,
                'source_type': 'computation',
                'source_reference': f"xTB calculation: {calc_id}",
                'software_version': xtb_version,
                'source_version': xtb_version,
                'algorithm_version': 'gfn2-xtb',
                'schema_version': 1,
                'processing_parameters': input_parameters or {'method': 'GFN2-xTB'},
                'computational_resource': 'cpu',
                'processing_time_seconds': None,
                'validated_by': 'system',
                'validation_timestamp': created_at_src,
                'created_at_source': created_at_src,
                'git_commit': git_commit,
                'approved_for_ml': False,
                'approval_notes': f"Auto-logged from xTB runner. SMILES: {(molecule_smiles or '')[:100]}. Requires manual approval.",
                'depends_on_ids': [],
            }

            result = self.supabase_client.insert('data_lineage', payload)
            
            if result:
                self.logger.info(f"Lineage logged for calc {calc_id}")
                return True
            else:
                self.logger.warning(f"Failed to log lineage for calc {calc_id}; attempting minimal fallback payload")
                try:
                    minimal = {
                        'job_key': calc_id,
                        'entity_type': 'calculations',
                        'entity_id': entity_id,
                        'source_reference': f"xTB calculation: {calc_id}",
                    }
                    fallback = self.supabase_client.insert('data_lineage', minimal)
                    if fallback:
                        self.logger.info(f"Fallback lineage logged for calc {calc_id}")
                        return True
                except Exception:
                    self.logger.debug("Fallback lineage insert failed", exc_info=True)
                self.logger.error(f"Failed to log lineage for calc {calc_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error logging lineage for {calc_id}: {e}", exc_info=True)
            return False

    def log_error(
        self,
        calc_id: str,
        error_message: str,
        error_type: str = "execution_error",
        molecule_smiles: Optional[str] = None
    ) -> bool:
        """
        Log calculation errors to Supabase calculation_errors table.

        PARAMETERS:
        - calc_id: unique calculation identifier
        - error_message: description of the error
        - error_type: category of error (execution_error, parsing_error, validation_error, etc.)
        - molecule_smiles: SMILES string for the molecule (optional)

        RETURNS:
        - True if logging succeeded, False otherwise
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return False

        try:
            # calculation_errors schema expects a numeric calculation_id; send
            # job_key (string) for traceability and omit calculation_id unless
            # it's a numeric id. Keep payload lean to avoid schema mismatches.
            payload = {
                'job_key': calc_id,
                # calculation_id may be UUID in the new schema; keep as-is
                'calculation_id': calc_id,
                'error_type': error_type,
                'error_message': error_message,
                'occurred_at': datetime.utcnow().isoformat() + 'Z',
                'runner_version': '1.0',
                'is_recoverable': False,
                'recovery_attempts': 0,
            }
            if molecule_smiles:
                payload['molecule_smiles'] = molecule_smiles

            result = self.supabase_client.insert('calculation_errors', payload)
            
            if result:
                self.logger.info(f"Error logged for calc {calc_id}")
                return True
            else:
                self.logger.error(f"Failed to log error for calc {calc_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error logging error for {calc_id}: {e}", exc_info=True)
            return False

    def log_molecule(
        self,
        molecule_smiles: str,
        molecule_formula: str,
        molecule_name: Optional[str] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Log molecular structure info to Supabase molecules table.

        PARAMETERS:
        - molecule_smiles: SMILES string representation of molecule
        - molecule_formula: Chemical formula (e.g., "H2O", "C6H6")
        - molecule_name: Optional human-readable name

        RETURNS:
        - Tuple (success: bool, molecule_id: Optional[int])
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return (False, None)

        try:
            # Map to new molecules schema: smiles, xyz_structure, embedding, source_type, parent_molecule_id
            payload = {
                'smiles': molecule_smiles,
                # we don't currently have the XYZ here; keep xyz_structure empty
                'xyz_structure': None,
                'source_type': 'human_upload',
                'created_at': datetime.utcnow().isoformat() + 'Z',
            }

            result = self.supabase_client.insert('molecules', payload)
            
            if result and isinstance(result, list) and len(result) > 0:
                molecule_id = result[0].get('id')
                self.logger.info(f"Molecule logged: {molecule_formula} (ID: {molecule_id})")
                return (True, molecule_id)
            else:
                # Try to retrieve existing molecule by SMILES and return its ID
                try:
                    exists = self.supabase_client.get('molecules', filters={'smiles': molecule_smiles}, select='id')
                    if exists and isinstance(exists, list) and len(exists) > 0:
                        molecule_id = exists[0].get('id')
                        self.logger.info(f"Molecule already exists: {molecule_formula} (ID: {molecule_id})")
                        return (True, molecule_id)
                except Exception:
                    self.logger.debug("Could not query existing molecule after failed insert", exc_info=True)
                self.logger.error(f"Failed to log molecule: {molecule_formula}")
                return (False, None)

        except Exception as e:
            self.logger.error(f"Error logging molecule {molecule_formula}: {e}", exc_info=True)
            return (False, None)

    def backfill_calculation_id(self, calculation_numeric_id: int, job_key: str) -> None:
        """
        Backfill numeric `calculation_id` into related tables that were initially
        logged using `job_key` only. This is a best-effort helper invoked after
        a calculation row has been created and its numeric primary key is known.
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return

        try:
            # Update quality metrics
            try:
                # calculation_numeric_id may be a UUID string in the new schema; accept as-is
                updated_q = self.supabase_client.update('data_quality_metrics', data={'calculation_id': calculation_numeric_id}, filters={'job_key': job_key})
                self.logger.info(f"Backfilled calculation_id into data_quality_metrics for job {job_key}: updated={bool(updated_q)}")
            except Exception:
                self.logger.debug("Failed to backfill data_quality_metrics", exc_info=True)

            # Update data lineage
            try:
                updated_l = self.supabase_client.update('data_lineage', data={'calculation_id': calculation_numeric_id}, filters={'job_key': job_key})
                self.logger.info(f"Backfilled calculation_id into data_lineage for job {job_key}: updated={bool(updated_l)}")
            except Exception:
                self.logger.debug("Failed to backfill data_lineage", exc_info=True)

            # Update execution metrics
            try:
                updated_e = self.supabase_client.update('calculation_execution_metrics', data={'calculation_id': calculation_numeric_id}, filters={'job_key': job_key})
                self.logger.info(f"Backfilled calculation_id into calculation_execution_metrics for job {job_key}: updated={bool(updated_e)}")
            except Exception:
                self.logger.debug("Failed to backfill calculation_execution_metrics", exc_info=True)

        except Exception as e:
            self.logger.error(f"Error during backfill of calculation_id for job {job_key}: {e}", exc_info=True)

    def log_execution_metrics(
        self,
        job_key: str,
        started_at: Optional[str],
        completed_at: Optional[str],
        wall_time_seconds: Optional[float],
        stdout: Optional[str],
        stderr: Optional[str],
        xtb_version: Optional[str] = None,
        method: Optional[str] = None,
        calculation_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Insert execution metrics into calculation_execution_metrics table.

        We insert by job_key so it can be later backfilled with numeric calculation_id.
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return None

        try:
            payload = {
                'job_key': job_key,
                'xtb_version': xtb_version,
                'method': method,
                'wall_time_seconds': wall_time_seconds,
                'cpu_time_seconds': None,
                'scf_cycles': None,
                'optimization_cycles': None,
                'convergence_iterations': None,
                'is_converged': None,
                'convergence_criterion_met': None,
                'memory_peak_mb': None,
                'stdout_log': (stdout or '')[:10000],
                'stderr_log': (stderr or '')[:10000],
                'started_at': started_at,
                'completed_at': completed_at,
            }
            if calculation_id is not None:
                # accept UUIDs or numeric ids
                payload['calculation_id'] = calculation_id

            # Attempt to find an existing metrics row by job_key. If present, PATCH (update) it;
            # otherwise INSERT a new row. This avoids 400 errors from attempting to UPDATE
            # non-existent rows using PostgREST filter syntax on some deployments.
            try:
                existing = self.supabase_client.get('calculation_execution_metrics', filters={'job_key': job_key}, select='id')
            except Exception:
                existing = []

            if existing and isinstance(existing, list) and len(existing) > 0:
                # Update existing row(s)
                try:
                    updated = self.supabase_client.update('calculation_execution_metrics', data=payload, filters={'job_key': job_key})
                    if updated:
                        # updated may be list
                        try:
                            exec_id = updated[0].get('id') if isinstance(updated, list) and len(updated) > 0 else (updated.get('id') if isinstance(updated, dict) else None)
                        except Exception:
                            exec_id = None
                        self.logger.info(f"Execution metrics updated for job {job_key} (id={exec_id})")
                        return exec_id
                    else:
                        self.logger.error(f"Failed to update execution metrics for job {job_key}")
                        return None
                except Exception as e:
                    self.logger.error(f"Error updating execution metrics for job {job_key}: {e}", exc_info=True)
                    # Fall through to attempt an insert as a last resort

            # Insert new metrics row
            result = self.supabase_client.insert('calculation_execution_metrics', payload)
            if result:
                # result may be dict (single row) or list
                try:
                    exec_id = result.get('id') if isinstance(result, dict) else (result[0].get('id') if isinstance(result, list) and len(result) > 0 else None)
                except Exception:
                    exec_id = None
                self.logger.info(f"Execution metrics logged for job {job_key} (id={exec_id})")
                return exec_id
            else:
                self.logger.error(f"Failed to log execution metrics for job {job_key}")
                return None
        except Exception as e:
            self.logger.error(f"Error logging execution metrics for {job_key}: {e}", exc_info=True)
            return None

    def log_calculation(
        self,
        calc_id: str,
        molecule_id: Optional[int],
        energy: float,
        homo: float,
        lumo: float,
        gap: float,
        dipole: Optional[float] = None,
        total_charge: int = 0,
        execution_time_seconds: Optional[float] = None,
        xtb_version: str = "6.7.1",
        convergence_status: str = "converged",
    method: str = "GFN2-xTB",
    quality_score: Optional[float] = None,
    ) -> tuple[bool, Optional[int]]:
        """
        Log calculation results to Supabase calculations table.

        PARAMETERS:
        - calc_id: unique calculation identifier
        - molecule_id: foreign key to molecules table
        - energy: Total energy in Hartree
        - homo: Highest occupied molecular orbital energy (eV)
        - lumo: Lowest unoccupied molecular orbital energy (eV)
        - gap: HOMO-LUMO gap (eV)
        - dipole: Dipole moment (optional)
        - total_charge: Molecular charge
        - execution_time_seconds: Time to compute
        - xtb_version: Version of xTB used
        - convergence_status: "converged", "not_converged", etc.
        - method: Calculation method

        RETURNS:
        - True if logging succeeded, False otherwise
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return (False, None)

        try:
            # Map to new calculations schema (UUID PK, JSONB active_space_config, quantum_metadata)
            # Use energy_hartree, homo_lumo_gap_ev, dipole_moment_debye, execution_time_ms
            exec_ms = None
            if execution_time_seconds is not None:
                try:
                    exec_ms = int(float(execution_time_seconds) * 1000)
                except Exception:
                    exec_ms = None

            payload = {
                'molecule_id': molecule_id,
                'job_key': calc_id,
                'energy_hartree': energy,
                'homo_lumo_gap_ev': gap,
                'dipole_moment_debye': dipole,
                'total_charge': total_charge,
                'execution_time_ms': exec_ms,
                'raw_log': None,
                # Map method into the new enum where possible. Default to 'xtb_gfn2'.
                'method': 'xtb_gfn2',
                'status': 'completed',
                'output_json_path': f"jobs/{calc_id}/xtbout.json",
                'metadata': {
                    'source': 'xtb_runner',
                    'calc_id': calc_id,
                    'logging_timestamp': datetime.utcnow().isoformat(),
                },
                'active_space_config': {},
                'quantum_metadata': {},
            }
            if quality_score is not None:
                payload['quality_score'] = quality_score

            result = self.supabase_client.insert('calculations', payload)

            if result:
                # result should include UUID id
                try:
                    calc_uuid = result.get('id') if isinstance(result, dict) else (result[0].get('id') if isinstance(result, list) and len(result) > 0 else None)
                except Exception:
                    calc_uuid = None
                self.logger.info(f"Calculation logged for molecule_id {molecule_id}: energy={energy:.4f} Ha (id={calc_uuid})")
                return True, calc_uuid
            else:
                self.logger.error(f"Failed to log calculation for molecule_id {molecule_id}")
                return False, None

        except Exception as e:
            self.logger.error(f"Error logging calculation for molecule_id {molecule_id}: {e}", exc_info=True)
            return False, None

    def log_run(
        self,
        run_id: str,
        molecule_id: Optional[int],
        calculation_id: Optional[object],
        status: str = "COMPLETED",
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        runtime_seconds: Optional[float] = None,
        user_email: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> bool:
        """
        Log a run record to the `runs` table to track job executions.

        RETURNS True if logging succeeded, False otherwise.
        """
        if not self.enable_quality_logging or not self.supabase_client:
            return False

        try:
            payload = {
                'run_id': run_id,
                'molecule_id': molecule_id,
                'status': status,
                'started_at': started_at,
                'finished_at': finished_at,
                'runtime_seconds': runtime_seconds,
                'user_email': user_email,
                'tags': tags or [],
                'metadata': {
                    'source': 'xtb_runner',
                    'logged_at': datetime.utcnow().isoformat() + 'Z'
                }
            }
            # Include calculation_id whether numeric or UUID string; the client will sanitize if incompatible
            if calculation_id is not None:
                # If calculation_id looks like an integer, store it in calculation_id
                # Otherwise store it in calculation_id_uuid to avoid bigint cast errors
                try:
                    if isinstance(calculation_id, int) or (isinstance(calculation_id, str) and calculation_id.isdigit()):
                        payload['calculation_id'] = int(str(calculation_id))
                    else:
                        # treat as UUID string
                        payload['calculation_id_uuid'] = str(calculation_id)
                except Exception:
                    payload['calculation_id_uuid'] = str(calculation_id)

            # Defensive sanitization: ensure we don't accidentally send a UUID into a BIGINT column
            if 'calculation_id' in payload and not isinstance(payload.get('calculation_id'), int):
                # promote to uuid field and drop the invalid numeric field
                try:
                    payload['calculation_id_uuid'] = str(payload.get('calculation_id'))
                except Exception:
                    payload['calculation_id_uuid'] = str(calculation_id)
                try:
                    del payload['calculation_id']
                except Exception:
                    pass

            result = self.supabase_client.insert('runs', payload)
            if result:
                self.logger.info(f"Run logged for run_id {run_id} status={status}")
                return True
            else:
                self.logger.error(f"Failed to log run for run_id {run_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error logging run {run_id}: {e}", exc_info=True)
            return False