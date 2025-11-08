import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging
import asyncio

from .schemas import JobSubmitRequest, JobStatus


class JobManager:
    """Manage xTB job submission, queueing, and execution"""
    
    def __init__(self, workdir: str = './jobs', logger=None):
        """
        Initialize JobManager
        
        Args:
            workdir: Directory to store job files
            logger: Logger instance
        """
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)
        
    def submit_job(self, job_request: JobSubmitRequest) -> str:
        """
        Submit a new job
        
        Args:
            job_request: Job submission request
            
        Returns:
            str: Unique job ID
        """
        # Generate unique job_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        job_id = f"{job_request.molecule_name}_{timestamp}_{unique_id}"
        
        # Create job directory
        job_dir = self.workdir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save xyz file
        xyz_path = job_dir / f"{job_request.molecule_name}.xyz"
        with open(xyz_path, 'w') as f:
            f.write(job_request.xyz_content)
        
        # Save job metadata
        job_metadata = {
            "job_id": job_id,
            "molecule_name": job_request.molecule_name,
            "optimization_level": job_request.optimization_level,
            "email": job_request.email,
            "tags": job_request.tags,
            "status": JobStatus.QUEUED,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "xyz_file": str(xyz_path.relative_to(self.workdir))
        }
        
        metadata_path = job_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(job_metadata, f, indent=2)
        
        self.logger.info(f"Job {job_id} created")
        
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict: Job status information or None if not found
        """
        job_dir = self.workdir / job_id
        
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
            
    async def execute_job(self, job_id: str) -> None:
        """
        Execute xTB job
        
        Args:
            job_id: Job identifier
        """
        job_dir = self.workdir / job_id
        
        if not job_dir.exists():
            self.logger.error(f"Job {job_id} not found")
            return
            
        # Update job status to RUNNING
        metadata_path = job_dir / "metadata.json"
        try:
            with open(metadata_path, 'r') as f:
                job_metadata = json.load(f)
                
            job_metadata["status"] = JobStatus.RUNNING
            job_metadata["updated_at"] = datetime.utcnow().isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(job_metadata, f, indent=2)
                
            self.logger.info(f"Job {job_id} status updated to RUNNING")
            
            # TODO: Execute xTB calculation using XTBRunner
            # This would integrate with the existing xTB automation system
            # For now, we'll simulate the execution
            
            await asyncio.sleep(2)  # Simulate processing time
            
            # Simulate results
            results = {
                "energy": -14.42,
                "homo_lumo_gap": 0.117,
                "gradient_norm": 0.0027,
                "charges": [0.1, -0.2, 0.15, -0.05, 0.0, 0.0],
                "convergence_status": "CONVERGED",
                "properties": {
                    "total_energy": -14.42,
                    "electronic_energy": -14.45,
                    "nuclear_repulsion_energy": 0.03,
                    "gradient_norm": 0.0027,
                    "homo_energy": -0.15,
                    "lumo_energy": -0.033,
                    "dipole_moment": 0.0
                }
            }
            
            # Save results
            results_path = job_dir / "results.json"
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Update job status to COMPLETED
            job_metadata["status"] = JobStatus.COMPLETED
            job_metadata["updated_at"] = datetime.utcnow().isoformat()
            job_metadata["results_file"] = str(results_path.relative_to(self.workdir))
            
            with open(metadata_path, 'w') as f:
                json.dump(job_metadata, f, indent=2)
                
            self.logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {str(e)}")
            
            # Update job status to FAILED
            try:
                with open(metadata_path, 'r') as f:
                    job_metadata = json.load(f)
                    
                job_metadata["status"] = JobStatus.FAILED
                job_metadata["error_message"] = str(e)
                job_metadata["updated_at"] = datetime.utcnow().isoformat()
                
                with open(metadata_path, 'w') as f:
                    json.dump(job_metadata, f, indent=2)
                    
            except Exception as update_error:
                self.logger.error(f"Error updating job status for {job_id}: {str(update_error)}")
                
    def list_jobs(self, status: str = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        List jobs with optional filtering
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List[Dict]: List of job information
        """
        jobs = []
        
        # Get all job directories
        job_dirs = [d for d in self.workdir.iterdir() if d.is_dir()]
        
        # Sort by creation time (newest first)
        job_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        
        # Apply offset and limit
        job_dirs = job_dirs[offset:offset + limit]
        
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
                    
        return jobs