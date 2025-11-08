"""
REST endpoints that trigger xTB execution.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
import json
from pathlib import Path
from datetime import datetime

from backend.config import XTBConfig, get_logger
from backend.api.job_manager import JobManager

# Configure logging
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1")

# Initialize configuration and job manager
try:
    xtb_config = XTBConfig()
    job_manager = JobManager(xtb_config, logger)
    logger.info("API routes initialized with xTB configuration")
except Exception as e:
    logger.error(f"Failed to initialize xTB configuration: {e}")
    raise


@router.post("/jobs/submit", status_code=201)
async def submit_job(job_request: Dict):
    """
    Submit a new xTB calculation job.
    
    - **molecule_name**: Name of the molecule
    - **xyz_content**: Raw XYZ file content
    - **optimization_level**: Optimization level (tight, normal, crude)
    - **email**: Email for notifications
    - **tags**: Tags for organizing results
    """
    try:
        # Validate molecule name
        if not job_request.get("molecule_name") or not job_request["molecule_name"].strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_MOLECULE_NAME",
                    "error_message": "Molecule name cannot be empty"
                }
            )
        
        # Validate XYZ content
        if not job_request.get("xyz_content") or not job_request["xyz_content"].strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_XYZ_CONTENT",
                    "error_message": "XYZ content cannot be empty"
                }
            )
        
        # Submit job
        job_id = job_manager.submit_job(job_request)
        
        logger.info(f"Job {job_id} submission accepted, async execution started")
        
        # Start async execution
        job_manager.run_job_async(job_id)
        
        # Return job response
        return {
            "job_id": job_id,
            "status": "QUEUED",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "results": None,
            "error_message": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_SUBMISSION_ERROR",
                "error_message": f"Failed to submit job: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a specific job.
    
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
        
        logger.info(f"Job status query for {job_id}")
        
        # If completed, include results
        if job_status.get("status") == "COMPLETED":
            job_dir = Path(xtb_config.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                job_status["results"] = results.get("results", {})
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_STATUS_ERROR",
                "error_message": f"Failed to retrieve job status: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """
    Get the results of a specific job.
    
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
        
        if status == "COMPLETED":
            # Return results
            job_dir = Path(xtb_config.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                logger.info(f"Results access for job {job_id}")
                return results.get("results", {})
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "RESULTS_NOT_FOUND",
                        "error_message": "Results file not found"
                    }
                )
        elif status == "RUNNING":
            # Return running status
            return {
                "status": "RUNNING",
                "progress": "Calculation in progress"
            }
        elif status == "FAILED":
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
        logger.error(f"Error retrieving job results for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_RESULTS_ERROR",
                "error_message": f"Failed to retrieve job results: {str(e)}"
            }
        )


@router.get("/jobs/list")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter jobs by status"),
    limit: int = Query(50, description="Number of jobs to return", ge=1, le=100)
):
    """
    List jobs with optional filtering by status.
    
    - **status**: Filter jobs by status (QUEUED, RUNNING, COMPLETED, FAILED)
    - **limit**: Number of jobs to return (1-100)
    """
    try:
        jobs = job_manager.list_jobs(status=status, limit=limit)
        
        logger.info(f"Job list query - status={status}, limit={limit}")
        return jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_LIST_ERROR",
                "error_message": f"Failed to list jobs: {str(e)}"
            }
        )