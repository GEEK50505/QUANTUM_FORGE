#!/usr/bin/env python3
"""
Test script for the XTB worker.

This script:
1. Creates a test queued job
2. Runs the worker for a short time
3. Verifies job completion
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import XTBConfig
from backend.db.job_store import JobStore
from services.worker.worker import Worker, WorkerConfig


def create_test_job():
    """Create a test water molecule job."""
    logger.info("Creating test job...")
    
    cfg = XTBConfig()
    job_store = JobStore(cfg.JOBS_DIR)
    
    # Create a simple water molecule XYZ
    xyz_content = """3
Water molecule
O   0.000000   0.000000   0.118720
H   0.000000   0.755453  -0.474880
H   0.000000  -0.755453  -0.474880
"""
    
    # Create job
    job_id = f"test_water_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    job_store.create_job_dir(job_id)
    job_store.save_xyz(job_id, "water", xyz_content)
    
    # Create metadata with QUEUED status
    metadata = {
        "job_id": job_id,
        "molecule_name": "water",
        "xyz_file": f"{job_id}/water.xyz",
        "status": "QUEUED",
        "optimization_level": "normal",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    job_store.save_metadata(job_id, metadata)
    logger.info(f"✓ Created test job: {job_id}")
    logger.info(f"  Metadata: {metadata}")
    
    return job_id, job_store


async def run_worker_test():
    """Run the worker and process the test job."""
    logger.info("=" * 60)
    logger.info("XTB Worker Test")
    logger.info("=" * 60)
    
    # Create test job
    job_id, job_store = create_test_job()
    
    # Create worker
    logger.info("\nInitializing worker...")
    worker = Worker()
    
    # Run worker for 120 seconds or until job completes
    logger.info(f"Running worker for up to 120 seconds...")
    logger.info(f"Watching for job {job_id}...\n")
    
    start_time = asyncio.get_event_loop().time()
    max_duration = 120  # seconds
    
    # Start worker
    worker_task = asyncio.create_task(worker.run())
    
    # Monitor job status
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Check job status
        metadata = job_store.load_metadata(job_id)
        if metadata:
            status = metadata.get('status')
            logger.info(f"[{elapsed:.1f}s] Job {job_id} status: {status}")
            
            if status == 'COMPLETED':
                logger.info(f"\n✓ Job completed successfully!")
                logger.info(f"  Energy: {metadata.get('energy')} Hartree")
                break
            elif status == 'FAILED':
                logger.error(f"\n✗ Job failed: {metadata.get('error')}")
                break
        
        # Timeout check
        if elapsed > max_duration:
            logger.warning(f"\n⏱ Timeout after {max_duration}s, stopping worker")
            break
        
        await asyncio.sleep(5)
    
    # Stop worker
    worker.running = False
    logger.info("\nStopping worker...")
    
    try:
        await asyncio.wait_for(worker_task, timeout=5)
    except asyncio.TimeoutError:
        logger.warning("Worker didn't stop gracefully, cancelling task")
        worker_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(run_worker_test())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
