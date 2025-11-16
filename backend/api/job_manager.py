"""
Manage job lifecycle with xTB integration.
"""
import uuid
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
from backend.config import XTBConfig
from backend.core.logging import get_logger
from backend.core.xtb_runner import XTBRunner
from backend.db.job_store import JobStore


class JobManager:
    """Manage job lifecycle with xTB integration."""

    def __init__(self, xtb_config: XTBConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize JobManager.

        Args:
            xtb_config: XTBConfig instance
            logger: Optional logger instance
        """
        self.xtb_config = xtb_config
        self.logger = logger or get_logger(__name__)
        self.logger.info("Initializing JobManager")

        # Initialize a JobStore to centralize filesystem operations
        self.job_store = JobStore(self.xtb_config.JOBS_DIR)
        # Ensure workdir exists as canonical runner expects it
        Path(self.xtb_config.WORKDIR).mkdir(parents=True, exist_ok=True)

    def submit_job(self, job_request: Dict) -> str:
        """
        Submit a new job.

        Args:
            job_request: Job request data

        Returns:
            Job ID
        """
        # Generate unique job_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        job_id = f"{job_request['molecule_name']}_{timestamp}_{unique_id}"

        self.logger.info(f"Job {job_id} submitted by {job_request.get('email', 'unknown')}")

        # Create job directory and save input via JobStore
        self.job_store.create_job_dir(job_id)
        xyz_path = self.job_store.save_xyz(job_id, job_request['molecule_name'], job_request['xyz_content'])

        job_metadata = {
            "job_id": job_id,
            "molecule_name": job_request['molecule_name'],
            # Accept optional SMILES and formula from frontend or API clients
            "molecule_smiles": job_request.get('molecule_smiles') or job_request.get('smiles'),
            "molecule_formula": job_request.get('molecule_formula'),
            "optimization_level": job_request.get('optimization_level', 'normal'),
            "email": job_request.get('email', ''),
            "tags": job_request.get('tags', []),
            "status": "QUEUED",
            # Use explicit UTC timestamps so clients parse times consistently
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "xyz_file": str(xyz_path.relative_to(self.xtb_config.JOBS_DIR))
        }

        self.job_store.save_metadata(job_id, job_metadata)
        self.logger.info(f"Job {job_id} created and queued")

        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status information or None if not found
        """
        job_metadata = self.job_store.load_metadata(job_id)
        if job_metadata is None:
            self.logger.warning(f"Job {job_id} not found or metadata missing")
            return None
        self.logger.info(f"Job status retrieved: {job_id}")
        return job_metadata

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its stored artifacts.

        Returns True if deleted, False if job not found or deletion failed.
        """
        # best-effort: stop any running threads is out-of-scope here
        try:
            removed = self.job_store.delete_job(job_id)
            if removed:
                self.logger.info(f"Job {job_id} deleted from store")
            else:
                self.logger.warning(f"Attempted to delete job {job_id} but it was not found")
            return removed
        except Exception as e:
            self.logger.error(f"Error deleting job {job_id}: {e}", exc_info=True)
            return False

    def execute_job(self, job_id: str) -> None:
        """
        Execute xTB job.

        Args:
            job_id: Job identifier
        """
        try:
            job_metadata = self.job_store.load_metadata(job_id)
            if job_metadata is None:
                self.logger.error(f"Job {job_id} not found")
                return

            job_metadata["status"] = "RUNNING"
            job_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            self.job_store.save_metadata(job_id, job_metadata)

            self.logger.info(f"Starting execution for job {job_id}")

            # Get XYZ file path
            xyz_file_path = Path(self.xtb_config.JOBS_DIR) / job_metadata["xyz_file"]

            # Execute xTB calculation with quality logging enabled
            self.logger.info(f"Instantiating XTBRunner with enable_quality_logging=True for job {job_id}")
            xtb_runner = XTBRunner(self.xtb_config, self.logger, enable_quality_logging=True)
            self.logger.info(f"XTBRunner initialized. supabase_client={'set' if xtb_runner.supabase_client else 'None'}, logging_enabled={xtb_runner.enable_quality_logging}")
            results = xtb_runner.execute(
                str(xyz_file_path),
                job_id,
                job_metadata.get("optimization_level", "normal")
            )

            if results["success"]:
                results_path = self.job_store.save_results(job_id, results)
                # Update job status to COMPLETED
                job_metadata["status"] = "COMPLETED"
                job_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
                job_metadata["results_file"] = str(results_path.relative_to(self.xtb_config.JOBS_DIR))
                self.logger.info(f"Job {job_id} completed successfully - Energy: {results['energy']}")
                
                # Log molecule and calculation metadata to Supabase
                try:
                    molecule_name = job_metadata.get("molecule_name", "unknown")
                    results_data = results.get("results", {})
                    
                    # Extract calculation data
                    energy = results_data.get("energy", results.get("energy", 0.0))
                    homo = results_data.get("homo", -7.5)
                    lumo = results_data.get("lumo", homo + results_data.get("gap", 0.0))
                    gap = results_data.get("gap", results_data.get("homo_lumo_gap", 0.0))
                    dipole = results_data.get("dipole")
                    
                    # Log molecule to molecules table
                    # Prefer SMILES or formula provided by the API/client if present
                    provided_smiles = job_metadata.get('molecule_smiles')
                    provided_formula = job_metadata.get('molecule_formula')

                    # If SMILES not provided, check if the molecule_name looks like a SMILES pattern
                    def looks_like_smiles(s: str) -> bool:
                        if not s:
                            return False
                        # Simple heuristic: SMILES contain characters like =#()[]+-/\\@ or digits for rings
                        return any(c in s for c in "=#()[]+-/\\@0123456789")

                    smiles_to_log = None
                    if provided_smiles:
                        smiles_to_log = provided_smiles
                    elif looks_like_smiles(molecule_name):
                        smiles_to_log = molecule_name

                    # Compute formula from the XYZ file if not provided
                    def compute_formula(xyz_path: Path) -> str:
                        """Simple XYZ->formula helper: counts atoms and returns string like C6H6"""
                        try:
                            with open(xyz_path, 'r') as f:
                                lines = [l.strip() for l in f.readlines() if l.strip()]
                            # Skip header lines
                            atom_lines = lines[2:]
                            counts: dict[str,int] = {}
                            for ln in atom_lines:
                                parts = ln.split()
                                if not parts:
                                    continue
                                elem = parts[0]
                                counts[elem] = counts.get(elem, 0) + 1
                            # Order: C, H, then alphabetical
                            order = []
                            if 'C' in counts:
                                order.append('C')
                            if 'H' in counts:
                                order.append('H')
                            for k in sorted(k for k in counts.keys() if k not in ['C','H']):
                                order.append(k)
                            parts = [f"{el}{counts[el] if counts[el] != 1 else ''}" for el in order]
                            return ''.join(parts) if parts else ''
                        except Exception:
                            return ''

                    formula_to_log = provided_formula
                    if not formula_to_log:
                        try:
                            xyz_path = Path(self.xtb_config.JOBS_DIR) / job_id / (molecule_name + '.xyz')
                            formula_to_log = compute_formula(xyz_path)
                        except Exception:
                            formula_to_log = ''

                    success, molecule_id = xtb_runner.log_molecule(
                        molecule_smiles=smiles_to_log or molecule_name,
                        molecule_formula=formula_to_log or molecule_name,
                        molecule_name=molecule_name
                    )
                    
                    if success and molecule_id:
                        # Log calculation to calculations table
                        # Compute quality score via the same QualityAssessor used during _assess_and_log_results
                        try:
                            qm = xtb_runner.quality_assessor.assess_calculation_quality(
                                calc_data=results_data,
                                calc_id=job_id,
                                computation_metadata={
                                    'xtb_version': '6.7.1',
                                    'optimization_level': job_metadata.get('optimization_level', 'normal')
                                }
                            )
                            quality_score = qm.overall_quality_score if qm else None
                        except Exception:
                            quality_score = None

                        xtb_runner.log_calculation(
                            calc_id=job_id,
                            molecule_id=molecule_id,
                            energy=energy,
                            homo=homo,
                            lumo=lumo,
                            gap=gap,
                            dipole=dipole if isinstance(dipole, float) else None,
                            total_charge=0,
                            execution_time_seconds=None,
                            xtb_version="6.7.1",
                            convergence_status="converged" if results["success"] else "unknown",
                            method="GFN2-xTB",
                            quality_score=quality_score,
                        )
                        self.logger.info(f"Logged molecule (ID: {molecule_id}) and calculation for job {job_id}")
                    else:
                        self.logger.warning(f"Failed to log molecule for job {job_id}")
                except Exception as logging_error:
                    self.logger.error(f"Error logging molecule/calculation for job {job_id}: {logging_error}", exc_info=True)
            else:
                # If the runner returned a failure (validation or execution),
                # attempt to record the error into Supabase so we have a record
                # of why the job failed. Prefer classifying invalid inputs as
                # validation_error to help downstream triage.
                try:
                    err_msg = results.get('error', '')
                    err_type = 'validation_error' if 'Invalid XYZ' in (err_msg or '') or 'overlapping' in (err_msg or '').lower() else 'execution_error'
                    # Try to include molecule SMILES if available for easier lookup
                    mol_smiles = job_metadata.get('molecule_smiles')
                    xtb_runner.log_error(calc_id=job_id, error_message=err_msg[:500], error_type=err_type, molecule_smiles=mol_smiles)
                except Exception as log_exc:
                    self.logger.debug(f"Could not log failure to Supabase for {job_id}: {log_exc}", exc_info=True)

                # Update job status to FAILED
                job_metadata["status"] = "FAILED"
                job_metadata["error_message"] = results["error"]
                job_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.logger.error(f"Job {job_id} failed: {results['error']}")

            # Save updated metadata
            self.job_store.save_metadata(job_id, job_metadata)

        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {str(e)}", exc_info=True)

            # Update job status to FAILED (best-effort)
            try:
                existing = self.job_store.load_metadata(job_id) or {}
                existing["status"] = "FAILED"
                existing["error_message"] = str(e)
                existing["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.job_store.save_metadata(job_id, existing)
            except Exception as update_error:
                self.logger.error(f"Error updating job status for {job_id}: {str(update_error)}")

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        List jobs with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of job information
        """
        # Delegate listing to JobStore
        jobs = self.job_store.list_jobs(status=status, limit=limit)
        self.logger.info(f"Listed {len(jobs)} jobs (status={status}, limit={limit})")
        return jobs

    def run_job_async(self, job_id: str) -> None:
        """
        Run job asynchronously in background thread.

        Args:
            job_id: Job identifier
        """
        self.logger.info(f"Starting async execution for job {job_id}")

        # Use threading to execute job in background
        thread = threading.Thread(target=self.execute_job, args=(job_id,))
        thread.daemon = True
        thread.start()

        self.logger.info(f"Job {job_id} thread started")