"""
Manage job lifecycle with xTB integration.
"""
import uuid
import logging
import threading
from datetime import datetime
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
            "optimization_level": job_request.get('optimization_level', 'normal'),
            "email": job_request.get('email', ''),
            "tags": job_request.get('tags', []),
            "status": "QUEUED",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
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
            job_metadata["updated_at"] = datetime.utcnow().isoformat()
            self.job_store.save_metadata(job_id, job_metadata)

            self.logger.info(f"Starting execution for job {job_id}")

            # Get XYZ file path
            xyz_file_path = Path(self.xtb_config.JOBS_DIR) / job_metadata["xyz_file"]

            # Execute xTB calculation
            xtb_runner = XTBRunner(self.xtb_config, self.logger)
            results = xtb_runner.execute(
                str(xyz_file_path),
                job_id,
                job_metadata.get("optimization_level", "normal")
            )

            if results["success"]:
                results_path = self.job_store.save_results(job_id, results)
                # Update job status to COMPLETED
                job_metadata["status"] = "COMPLETED"
                job_metadata["updated_at"] = datetime.utcnow().isoformat()
                job_metadata["results_file"] = str(results_path.relative_to(self.xtb_config.JOBS_DIR))
                self.logger.info(f"Job {job_id} completed successfully - Energy: {results['energy']}")
            else:
                # Update job status to FAILED
                job_metadata["status"] = "FAILED"
                job_metadata["error_message"] = results["error"]
                job_metadata["updated_at"] = datetime.utcnow().isoformat()
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
                existing["updated_at"] = datetime.utcnow().isoformat()
                self.job_store.save_metadata(job_id, existing)
            except Exception as update_error:
                self.logger.error(f"Error updating job status for {job_id}: {str(update_error)}")

    def list_jobs(self, status: str = None, limit: int = 50) -> List[Dict]:
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