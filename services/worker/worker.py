import asyncio
import logging
import json
import sys
import traceback
import time
from datetime import datetime, timezone
from typing import Any, Optional, Dict
from pathlib import Path

# Set up logging immediately
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Try importing backend dependencies with detailed error handling
try:
    from backend.config import XTBConfig, get_logger
    logger.info("✓ XTBConfig imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import XTBConfig: {e}")
    sys.exit(1)

try:
    from backend.core.xtb_runner import XTBRunner
    logger.info("✓ XTBRunner imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import XTBRunner: {e}")
    sys.exit(1)

try:
    from backend.db.job_store import JobStore
    logger.info("✓ JobStore imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import JobStore: {e}")
    sys.exit(1)


class WorkerConfig:
    """Configuration for the worker service."""
    
    def __init__(self):
        self.worker_id = "worker_1"
        self.max_concurrent_jobs = 3
        self.job_timeout = 3600  # 1 hour (matches XTB_TIMEOUT)
        self.poll_interval = 5  # seconds between polling for new jobs
        self.health_check_interval = 30  # seconds
        
        logger.info(f"WorkerConfig initialized: worker={self.worker_id}, poll_interval={self.poll_interval}s, timeout={self.job_timeout}s")


class Worker:
    """
    Production Worker service for processing XTB jobs from the filesystem job store.
    
    Responsibilities:
    - Poll filesystem for queued jobs
    - Execute XTB calculations on queued jobs
    - Track job progress and update job status
    - Handle timeouts and errors gracefully
    - Report status and metrics
    """
    
    def __init__(self, config: Optional[WorkerConfig] = None, xtb_config: Optional[XTBConfig] = None):
        self.config = config or WorkerConfig()
        self.xtb_config = xtb_config or XTBConfig()
        
        # Initialize job store and XTB runner
        self.job_store = JobStore(self.xtb_config.JOBS_DIR)
        self.xtb_runner = XTBRunner(self.xtb_config, enable_quality_logging=True)
        
        self.running = False
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)
        
        logger.info(f"Worker initialized: id={self.config.worker_id}, max_concurrent={self.config.max_concurrent_jobs}")
        logger.info(f"XTB Config: timeout={self.xtb_config.XTB_TIMEOUT}s, workdir={self.xtb_config.WORKDIR}")
    
    async def poll_for_jobs(self) -> list[Dict[str, Any]]:
        """
        Poll the job store for queued jobs.
        
        Returns:
            List of job metadata dictionaries with status='QUEUED'
        """
        try:
            jobs = self.job_store.list_jobs(status='QUEUED', limit=10)
            if jobs:
                logger.info(f"Found {len(jobs)} queued jobs")
            return jobs
        except Exception as e:
            logger.error(f"✗ Error polling for jobs: {e}")
            return []
    
    async def execute_job_async(self, job_id: str, job_metadata: Dict[str, Any]) -> None:
        """
        Execute a single job asynchronously with proper error handling and status updates.
        
        Args:
            job_id: Job identifier
            job_metadata: Job metadata dictionary
        """
        async with self.job_semaphore:
            self.active_jobs[job_id] = {
                'start_time': datetime.now(timezone.utc),
                'status': 'RUNNING'
            }
            
            try:
                logger.info(f"Starting execution for job {job_id}")
                
                # Update job status to RUNNING
                job_metadata['status'] = 'RUNNING'
                job_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                self.job_store.save_metadata(job_id, job_metadata)
                
                # Get XYZ file path
                xyz_file_path = Path(self.xtb_config.JOBS_DIR) / job_metadata.get('xyz_file', '')
                
                if not xyz_file_path.exists():
                    logger.error(f"✗ XYZ file not found: {xyz_file_path}")
                    raise FileNotFoundError(f"XYZ file not found: {xyz_file_path}")
                
                logger.info(f"XYZ file: {xyz_file_path}")
                
                # Execute with timeout
                try:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.xtb_runner.execute,
                            str(xyz_file_path),
                            job_id,
                            job_metadata.get('optimization_level', 'normal')
                        ),
                        timeout=self.config.job_timeout
                    )
                    
                    if result.get('success'):
                        logger.info(f"✓ Job {job_id} completed successfully")
                        logger.info(f"  Energy: {result.get('energy')} Hartree")
                        
                        # Update job status to COMPLETED
                        job_metadata['status'] = 'COMPLETED'
                        job_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                        job_metadata['energy'] = result.get('energy')
                        self.job_store.save_metadata(job_id, job_metadata)
                        
                        # Save detailed results
                        self.job_store.save_results(job_id, result)
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        logger.error(f"✗ Job {job_id} failed: {error_msg}")
                        
                        job_metadata['status'] = 'FAILED'
                        job_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                        job_metadata['error'] = error_msg
                        self.job_store.save_metadata(job_id, job_metadata)
                        
                except asyncio.TimeoutError:
                    logger.error(f"✗ Job {job_id} timed out after {self.config.job_timeout}s")
                    job_metadata['status'] = 'FAILED'
                    job_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                    job_metadata['error'] = f'Job timeout after {self.config.job_timeout}s'
                    self.job_store.save_metadata(job_id, job_metadata)
                    
            except Exception as e:
                logger.error(f"✗ Unexpected error executing job {job_id}: {e}")
                logger.error(f"  Traceback: {traceback.format_exc()}")
                
                try:
                    job_metadata['status'] = 'FAILED'
                    job_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                    job_metadata['error'] = str(e)
                    self.job_store.save_metadata(job_id, job_metadata)
                except Exception as update_error:
                    logger.error(f"✗ Failed to update metadata for job {job_id}: {update_error}")
                    
            finally:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
                logger.info(f"Job {job_id} execution complete, cleaning up")
    
    async def health_check(self) -> None:
        """Periodically log worker health status."""
        while self.running:
            try:
                active_count = len(self.active_jobs)
                logger.info(f"Health check: active_jobs={active_count}, status=healthy, worker={self.config.worker_id}")
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"✗ Health check error: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    async def job_polling_loop(self) -> None:
        """Main job polling loop - continuously checks for and processes queued jobs."""
        logger.info("Starting job polling loop...")
        
        while self.running:
            try:
                # Poll for queued jobs
                queued_jobs = await self.poll_for_jobs()
                
                # Submit each job for execution
                for job_metadata in queued_jobs:
                    job_id = job_metadata.get('job_id')
                    if not job_id:
                        logger.warning("Job metadata missing job_id, skipping")
                        continue
                    
                    logger.info(f"Submitting job {job_id} for execution")
                    # Fire and forget - execute job asynchronously
                    asyncio.create_task(self.execute_job_async(job_id, job_metadata))
                
                # Sleep before next poll
                await asyncio.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error(f"✗ Error in polling loop: {e}")
                logger.error(f"  Traceback: {traceback.format_exc()}")
                await asyncio.sleep(self.config.poll_interval)
    
    async def run(self) -> None:
        """
        Main worker loop.
        
        Starts the job polling loop and health check monitoring.
        """
        logger.info("Starting Worker...")
        self.running = True
        
        try:
            # Create background tasks
            health_task = asyncio.create_task(self.health_check())
            polling_task = asyncio.create_task(self.job_polling_loop())
            
            logger.info(f"Worker listening for jobs every {self.config.poll_interval}s...")
            
            # Wait for either task to fail (shouldn't happen unless error)
            await asyncio.gather(health_task, polling_task)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"✗ Fatal error in worker: {e}")
            logger.error(f"  Traceback: {traceback.format_exc()}")
        finally:
            self.running = False
            logger.info("Worker shut down complete")


async def main():
    """Entry point for the worker service."""
    logger.info("=" * 60)
    logger.info("QUANTUM FORGE - Production XTB Worker")
    logger.info("=" * 60)
    
    try:
        worker = Worker()
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"✗ Fatal error: {e}")
        logger.error(f"  Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

