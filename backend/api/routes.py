from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid
import os
import json
from pathlib import Path

from .schemas import (
    JobSubmitRequest, 
    JobResponse, 
    ResultsResponse, 
    JobStatus
)
from .job_manager import JobManager
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1")

# Initialize job manager
job_manager = JobManager(workdir=Config.JOBS_DIR, logger=logger)


def get_job_manager():
    """Dependency injection for job manager"""
    return job_manager


@router.post("/jobs/submit", response_model=JobResponse, status_code=201)
async def submit_job(
    job_request: JobSubmitRequest,
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Submit a new xTB calculation job
    
    - **molecule_name**: Name of the molecule
    - **xyz_content**: Raw XYZ file content
    - **optimization_level**: Optimization level (tight or normal)
    - **email**: Email for notifications
    - **tags**: Tags for organizing results
    """
    try:
        # Validate molecule name
        if not job_request.molecule_name or not job_request.molecule_name.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_MOLECULE_NAME",
                    "error_message": "Molecule name cannot be empty"
                }
            )
        
        # Validate XYZ content
        if not job_request.xyz_content or not job_request.xyz_content.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_XYZ_CONTENT",
                    "error_message": "XYZ content cannot be empty"
                }
            )
        
        # Submit job
        job_id = job_manager.submit_job(job_request)
        
        logger.info(f"Job {job_id} submitted for {job_request.molecule_name}")
        
        # Return job response
        return JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            results=None,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_SUBMISSION_ERROR",
                "error_message": f"Failed to submit job: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Get the status of a specific job
    
    - **job_id**: Unique identifier of the job
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found"
                }
            )
        
        logger.info(f"Job status requested: {job_id}")
        
        return JobResponse(**job_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_STATUS_ERROR",
                "error_message": f"Failed to retrieve job status: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}/results")
async def get_job_results(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Get the results of a specific job
    
    - **job_id**: Unique identifier of the job
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found"
                }
            )
        
        status = job_status.get("status")
        
        if status == JobStatus.COMPLETED:
            # Return results
            results_path = Path(Config.JOBS_DIR) / job_id / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                logger.info(f"Results retrieved: {job_id}")
                return ResultsResponse(**results)
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "RESULTS_NOT_FOUND",
                        "error_message": "Results file not found"
                    }
                )
        elif status == JobStatus.RUNNING:
            # Return running status
            return {
                "status": "RUNNING",
                "progress": "Calculation in progress"
            }
        elif status == JobStatus.FAILED:
            # Return error
            return {
                "error": job_status.get("error_message", "Job failed")
            }
        else:
            # Return queued status
            return {
                "status": status,
                "message": "Job is queued and waiting to be processed"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job results for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_RESULTS_ERROR",
                "error_message": f"Failed to retrieve job results: {str(e)}"
            }
        )


@router.get("/jobs/list", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter jobs by status"),
    limit: int = Query(50, description="Number of jobs to return", ge=1, le=100),
    offset: int = Query(0, description="Number of jobs to skip", ge=0),
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    List jobs with optional filtering by status
    
    - **status**: Filter jobs by status (QUEUED, RUNNING, COMPLETED, FAILED)
    - **limit**: Number of jobs to return (1-100)
    - **offset**: Number of jobs to skip
    """
    try:
        jobs = job_manager.list_jobs(
            status=status.value if status else None,
            limit=limit,
            offset=offset
        )
        
        return [JobResponse(**job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_LIST_ERROR",
                "error_message": f"Failed to list jobs: {str(e)}"
            }
        )


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    Delete or cancel a job
    
    - **job_id**: Unique identifier of the job
    """
    try:
        job_status = job_manager.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found"
                }
            )
        
        # For now, we'll just log the deletion
        # In a production system, you might want to cancel running jobs
        logger.info(f"Job deleted: {job_id}")
        
        # Remove job directory
        job_dir = Path(Config.JOBS_DIR) / job_id
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_DELETE_ERROR",
                "error_message": f"Failed to delete job: {str(e)}"
            }
        )