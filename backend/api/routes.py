"""
REST endpoints that trigger xTB execution.

This module exposes the HTTP endpoints used by the frontend. Initialization
of the xTB configuration and JobManager is done lazily so that importing the
module doesn't crash the process if xTB is not present.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import json
from pathlib import Path
from datetime import datetime

from backend.config import XTBConfig, get_logger
from backend.api.job_manager import JobManager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1")

# Lazy-init containers
xtb_config = None
job_manager = None


def _get_manager():
    global xtb_config, job_manager
    if job_manager is None or xtb_config is None:
        try:
            xtb_config = XTBConfig()
            job_manager = JobManager(xtb_config, logger)
            logger.info("API routes initialized with xTB configuration")
        except Exception as e:
            logger.error("Failed to initialize xTB configuration", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "XTB_CONFIG_ERROR",
                    "error_message": f"xTB configuration not available: {str(e)}",
                },
            )
    return job_manager, xtb_config


def _normalize_job_for_api(job: Dict) -> Dict:
    out = dict(job)
    status = out.get("status")
    if isinstance(status, str):
        out["status"] = status.lower()
    return out


@router.post("/jobs/submit", status_code=201)
async def submit_job(job_request: Dict):
    try:
        jm, cfg = _get_manager()

        if not job_request.get("molecule_name") or not job_request["molecule_name"].strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_MOLECULE_NAME",
                    "error_message": "Molecule name cannot be empty",
                },
            )

        if not job_request.get("xyz_content") or not job_request["xyz_content"].strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_XYZ_CONTENT",
                    "error_message": "XYZ content cannot be empty",
                },
            )

        job_id = jm.submit_job(job_request)
        logger.info(f"Job {job_id} submission accepted, async execution started")

        jm.run_job_async(job_id)
        job_metadata = jm.get_job_status(job_id)
        if job_metadata:
            return _normalize_job_for_api(job_metadata)

        return {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "results": None,
            "error_message": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error submitting job", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_SUBMISSION_ERROR",
                "error_message": f"Failed to submit job: {str(e)}",
            },
        )


@router.get("/jobs/list")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter jobs by status"),
    limit: int = Query(50, description="Number of jobs to return", ge=1, le=100),
):
    try:
        jm, cfg = _get_manager()
        status_query = status.upper() if isinstance(status, str) else None
        jobs = jm.list_jobs(status=status_query, limit=limit)

        enriched = []
        for j in jobs:
            try:
                if j.get("status") == "COMPLETED":
                    job_dir = Path(cfg.JOBS_DIR) / j["job_id"]
                    results_path = job_dir / "results.json"

                    # Defensive: if metadata already contains an embedded 'results' key
                    # but the on-disk results.json is missing or job directory is absent,
                    # remove the embedded results to avoid returning stale/mismatched data
                    if j.get('results') and not results_path.exists():
                        logger.debug(f"Removing embedded results for job {j.get('job_id')} because {results_path} is missing")
                        j.pop('results', None)

                    # Load results from the job's results.json when available
                    if results_path.exists():
                        with open(results_path, "r") as f:
                            data = json.load(f)
                        results_obj = data.get("results") if isinstance(data, dict) and "results" in data else data
                        j["results"] = results_obj if isinstance(results_obj, dict) else {}
            except Exception:
                logger.debug(f"Could not load results for job {j.get('job_id')}")

            enriched.append(_normalize_job_for_api(j))

        return JSONResponse(status_code=200, content=enriched)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing jobs", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_LIST_ERROR",
                "error_message": f"Failed to list jobs: {str(e)}",
            },
        )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    try:
        jm, cfg = _get_manager()
        job_status = jm.get_job_status(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found",
                },
            )

        if job_status.get("status") == "COMPLETED":
            job_dir = Path(cfg.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, "r") as f:
                    results = json.load(f)
                results_obj = results.get("results") if isinstance(results, dict) and "results" in results else results
                job_status["results"] = results_obj if isinstance(results_obj, dict) else {}

        return _normalize_job_for_api(job_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving job status", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_STATUS_ERROR",
                "error_message": f"Failed to retrieve job status: {str(e)}",
            },
        )


@router.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    try:
        jm, cfg = _get_manager()
        job_status = jm.get_job_status(job_id)

        if not job_status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found",
                },
            )

        status = job_status.get("status")
        if status == "COMPLETED":
            job_dir = Path(cfg.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, "r") as f:
                    results = json.load(f)
                results_obj = results.get("results") if isinstance(results, dict) and "results" in results else results
                return results_obj if isinstance(results_obj, dict) else {}
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "RESULTS_NOT_FOUND",
                        "error_message": "Results file not found",
                    },
                )
        elif status == "RUNNING":
            return {"status": "running", "progress": "Calculation in progress"}
        elif status == "FAILED":
            return {"status": "failed", "error": job_status.get("error_message", "Job failed")}
        else:
            return {"status": (status.lower() if isinstance(status, str) else status), "message": "Job is queued and waiting to be processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving results", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_RESULTS_ERROR",
                "error_message": f"Failed to retrieve job results: {str(e)}",
            },
        )


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    try:
        jm, cfg = _get_manager()
        removed = jm.delete_job(job_id)
        if not removed:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found",
                },
            )
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting job", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_DELETE_ERROR",
                "error_message": f"Failed to delete job: {str(e)}",
            },
        )
"""
REST endpoints that trigger xTB execution.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
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

# Initialize configuration and job manager lazily. Avoid raising on import so tests
# or tooling that import this module without xTB installed won't fail immediately.
xtb_config = None
job_manager = None


def _get_manager():
    """Ensure xtb_config and job_manager are initialized and return them.

    If initialization fails (e.g. xTB missing), raise an HTTPException so the
    API returns a 500 to callers instead of failing import-time.
    """
    global xtb_config, job_manager
    if job_manager is None or xtb_config is None:
        try:
            xtb_config = XTBConfig()
            job_manager = JobManager(xtb_config, logger)
            logger.info("API routes initialized with xTB configuration")
        except Exception as e:
            logger.error(f"Failed to initialize xTB configuration: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "XTB_CONFIG_ERROR",
                    "error_message": f"xTB configuration not available: {str(e)}"
                }
            )
    return job_manager, xtb_config


def _normalize_job_for_api(job: Dict) -> Dict:
    """Return a copy of job metadata adapted for the API (lowercase status).

    This keeps internal storage (which may use UPPERCASE statuses) separate
    from the API contract expected by the frontend (lowercase statuses).
    """
    out = dict(job)
    status = out.get('status')
    if isinstance(status, str):
        out['status'] = status.lower()
    return out


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
        jm, cfg = _get_manager()

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
        job_id = jm.submit_job(job_request)
        logger.info(f"Job {job_id} submission accepted, async execution started")

        # Start async execution
        jm.run_job_async(job_id)

        # Return the canonical metadata that was written to the job store so
        # the frontend receives the same timestamps and fields the server
        # persisted (normalize status to frontend-friendly lowercase).
        job_metadata = jm.get_job_status(job_id)
        if job_metadata:
            return _normalize_job_for_api(job_metadata)

        # Fallback: return a minimal queued response
        return {
            "job_id": job_id,
            "status": "queued",
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


@router.get("/jobs/list")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter jobs by status"),
    limit: int = Query(50, description="Number of jobs to return", ge=1, le=100)
):
    """
    List jobs with optional filtering by status.
    
    - **status**: Filter jobs by status (queued, running, completed, failed)
    - **limit**: Number of jobs to return (1-100)
    """
    try:
        logger.debug(f"Listing jobs requested - status={status}, limit={limit}")

        # Normalize status filter: frontend sends lowercase values; internal storage uses UPPERCASE.
        jm, cfg = _get_manager()
        status_query = status.upper() if isinstance(status, str) else None
        jobs = jm.list_jobs(status=status_query, limit=limit)
        logger.info(f"Job list query - status={status}, limit={limit} -> found={len(jobs)}")

        # For completed jobs, include the results payload (if available).
        enriched = []
        for j in jobs:
            try:
                if j.get('status') == 'COMPLETED':
                    job_dir = Path(cfg.JOBS_DIR) / j['job_id']
                    results_path = job_dir / 'results.json'
                    if results_path.exists():
                        with open(results_path, 'r') as f:
                            data = json.load(f)
                        # Unwrap wrapper shape: prefer data['results'] when present
                        results_obj = data.get('results') if isinstance(data, dict) and 'results' in data else data
                        j['results'] = results_obj if isinstance(results_obj, dict) else {}
            except Exception:
                # Don't fail the whole listing if one job's results can't be read
                logger.debug(f"Could not load results for job {j.get('job_id')}")

            # Normalize before returning to frontend
            enriched.append(_normalize_job_for_api(j))

        # Always return 200 with job array (possibly empty).
        return JSONResponse(status_code=200, content=enriched)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_LIST_ERROR",
                "error_message": f"Failed to list jobs: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a specific job.
    
    - **job_id**: Unique identifier of the job
    """
    try:
        jm, cfg = _get_manager()
        job_status = jm.get_job_status(job_id)

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
            job_dir = Path(cfg.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                # Unwrap wrapper shape if necessary
                results_obj = results.get('results') if isinstance(results, dict) and 'results' in results else results
                job_status["results"] = results_obj if isinstance(results_obj, dict) else {}

        # Normalize job before returning to frontend (lowercase status)
        return _normalize_job_for_api(job_status)

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
        jm, cfg = _get_manager()
        job_status = jm.get_job_status(job_id)

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
            job_dir = Path(cfg.JOBS_DIR) / job_id
            results_path = job_dir / "results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    results = json.load(f)
                logger.info(f"Results access for job {job_id}")
                # Unwrap wrapper if needed
                results_obj = results.get('results') if isinstance(results, dict) and 'results' in results else results
                return results_obj if isinstance(results_obj, dict) else {}
            else:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "RESULTS_NOT_FOUND",
                        "error_message": "Results file not found"
                    }
                )
        elif status == "RUNNING":
            # Return running status (normalized)
            return {"status": "running", "progress": "Calculation in progress"}
        elif status == "FAILED":
            # Return error (normalized)
            return {"status": "failed", "error": job_status.get("error_message", "Job failed")}
        else:
            # Return queued/other status mapped to lowercase
            return {"status": (status.lower() if isinstance(status, str) else status), "message": "Job is queued and waiting to be processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_RESULTS_ERROR",
                "error_message": f"Failed to retrieve job results: {str(e)}"
            }
        )

@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """
    Delete a job and all stored artifacts.
    """
    try:
        jm, cfg = _get_manager()
        removed = jm.delete_job(job_id)
        if not removed:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "JOB_NOT_FOUND",
                    "error_message": f"Job {job_id} not found"
                }
            )
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "JOB_DELETE_ERROR",
                "error_message": f"Failed to delete job: {str(e)}"
            }
        )
