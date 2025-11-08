"""
Manage job lifecycle with xTB integration.
"""
import os
import json
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from backend.config import XTBConfig, AppConfig, get_logger
from backend.core.xtb_runner import XTBRunner


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
        
        # Create directories
        Path(self.xtb_config.JOBS_DIR).mkdir(parents=True, exist_ok=True)
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
        
        # Create job directory
        job_dir = Path(self.xtb_config.JOBS_DIR) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save xyz file
        xyz_path = job_dir / f"{job_request['molecule_name']}.xyz"
        with open(xyz_path, 'w') as f:
            f.write(job_request['xyz_content'])
        
        # Save job metadata
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
        
        metadata_path = job_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(job_metadata, f, indent=2)
        
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
        job_dir = Path(self.xtb_config.JOBS_DIR) / job_id
        
        if not job_dir.exists():
            self.logger.warning(f"Job {job_id} not found")
            return None
            
        metadata_path = job_dir / "metadata.json"
        if not metadata_path.exists():
            self.logger.error(f"Metadata file not found for job {job_id}")
            return None
            
        try:
            with open(metadata_path, 'r') as f:
                job_metadata = json.load(f)
                
            self.logger.info(f"Job status retrieved: {job_id}")
            return job_metadata
            
        except Exception as e:
            self.logger.error(f"Error reading job metadata for {job_id}: {str(e)}")
            return None
    
    def execute_job(self, job_id: str) -> None:
        """
        Execute xTB job.
        
        Args:
            job_id: Job identifier
        """
        job_dir = Path(self.xtb_config.JOBS_DIR) / job_id
        
        if not job_dir.exists():
            self.logger.error(f"Job {job_id} not found")
            return
        
        # Update job status to RUNNING
        metadata_path = job_dir / "metadata.json"
        try:
            with open(metadata_path, 'r') as f:
                job_metadata = json.load(f)
                
            job_metadata["status"] = "RUNNING"
            job_metadata["updated_at"] = datetime.utcnow().isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(job_metadata, f, indent=2)
                
            self.logger.info(f"Starting execution for job {job_id}")
            
            # Get XYZ file path
            xyz_file_path = job_dir / job_metadata["xyz_file"]
            
            # Execute xTB calculation
            xtb_runner = XTBRunner(self.xtb_config, self.logger)
            results = xtb_runner.execute(
                str(xyz_file_path),
                job_id,
                job_metadata.get("optimization_level", "normal")
            )
            
            if results["success"]:
                # Save results
                results_path = job_dir / "results.json"
                with open(results_path, 'w') as f:
                    json.dump(results, f, indent=2)
                
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
            with open(metadata_path, 'w') as f:
                json.dump(job_metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {str(e)}", exc_info=True)
            
            # Update job status to FAILED
            try:
                with open(metadata_path, 'r') as f:
                    job_metadata = json.load(f)
                    
                job_metadata["status"] = "FAILED"
                job_metadata["error_message"] = str(e)
                job_metadata["updated_at"] = datetime.utcnow().isoformat()
                
                with open(metadata_path, 'w') as f:
                    json.dump(job_metadata, f, indent=2)
                    
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
        jobs = []
        
        # Get all job directories
        jobs_dir = Path(self.xtb_config.JOBS_DIR)
        if not jobs_dir.exists():
            return []
            
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
        
        # Sort by creation time (newest first)
        job_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        
        # Apply limit
        job_dirs = job_dirs[:limit]
        
        for job_dir in job_dirs:
            metadata_path = job_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        job_metadata = json.load(f)
                        
                    # Filter by status if provided
                    if status is None or job_metadata.get("status") == status:
                        jobs.append(job_metadata)
                        
                except Exception as e:
                    self.logger.error(f"Error reading metadata for job {job_dir.name}: {str(e)}")
                    continue
                    
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