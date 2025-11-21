"""
PGMQ-based Worker for QUANTUM_FORGE

This worker attempts to use the Postgres pgmq extension first. If pgmq
is not available it will gracefully fall back to the existing filesystem
`JobStore` polling approach.

Notes:
- This is a pragmatic starter implementation. Adjust SQL calls to match
  your pgmq installation / function signatures if different.
- The worker expects `DATABASE_URL` in the environment.

Usage:
  . .venv/bin/activate
  export DATABASE_URL=postgresql://user:pass@host:5432/dbname
  python services/worker/pgmq_worker.py

"""
import os
import time
import json
import logging
import traceback
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg2
import psycopg2.extras
from backend.db.supabase_job_store import SupabaseJobStore
import functools

# Local imports (project)
try:
    from backend.config import XTBConfig
    from backend.core.xtb_runner import XTBRunner
    from backend.db.job_store import JobStore
except Exception:
    # If running outside the project root in tests, allow failure to import
    XTBConfig = None
    XTBRunner = None
    JobStore = None


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pgmq_worker')


class PGMQWorkerConfig:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.queue_name = os.getenv('PGMQ_QUEUE', 'xtb_calculation_queue')
        self.poll_interval = int(os.getenv('WORKER_POLL_INTERVAL', '3'))
        self.batch_size = int(os.getenv('WORKER_BATCH_SIZE', '5'))
        self.visibility_timeout = int(os.getenv('WORKER_VT', '300'))
        self.max_concurrent = int(os.getenv('WORKER_MAX_CONCURRENT', '3'))
        self.job_timeout = int(os.getenv('WORKER_JOB_TIMEOUT', '3600'))


class PGMQWorker:
    def __init__(self, cfg: Optional[PGMQWorkerConfig] = None):
        self.cfg = cfg or PGMQWorkerConfig()
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.running = False

        # Initialize XTB runner and JobStore if available
        self.xtb_cfg = XTBConfig() if XTBConfig is not None else None
        self.xtb_runner = XTBRunner(self.xtb_cfg) if XTBRunner is not None and self.xtb_cfg is not None else None
        self.job_store = JobStore(self.xtb_cfg.JOBS_DIR) if JobStore is not None and self.xtb_cfg is not None else None

        # Supabase/pgmq store (adapter) - only create if DATABASE_URL provided
        if self.cfg.database_url:
            self.supabase_store = SupabaseJobStore(self.cfg.database_url, queue_name=self.cfg.queue_name)
        else:
            self.supabase_store = None

        # Concurrency semaphore
        self.semaphore = asyncio.Semaphore(self.cfg.max_concurrent)

    def connect_db(self):
        if not self.cfg.database_url:
            raise RuntimeError('DATABASE_URL environment variable not set')
        # Initialize supabase job store connection
        if not self.supabase_store:
            raise RuntimeError('SupabaseJobStore not configured (DATABASE_URL missing)')
        self.supabase_store.connect()
        logger.info('Connected to Postgres via SupabaseJobStore')

    def pgmq_available(self) -> bool:
        try:
            if not self.supabase_store:
                return False
            return self.supabase_store.pgmq_available()
        except Exception:
            return False

    def read_pgmq_batch(self):
        """Read a batch of messages from pgmq. Returns list of rows (raw)."""
        if not self.supabase_store:
            return []
        return self.supabase_store.read_pgmq(self.cfg.batch_size, self.cfg.visibility_timeout)

    def archive_pgmq(self, msg_id):
        try:
            if not self.supabase_store:
                return
            self.supabase_store.archive_pgmq(msg_id)
        except Exception as e:
            logger.error('pgmq.archive failed for %s: %s', msg_id, e)

    async def _process_job_from_payload(self, job_payload: Dict[str, Any], msg_id: Any):
        """Core job execution using XTBRunner. job_payload should include job_key or xyz path."""
        async with self.semaphore:
            # Guard payload
            if not job_payload or not isinstance(job_payload, dict):
                job_payload = {}

            job_key = job_payload.get('job_key') or job_payload.get('job_id')
            # Ensure a safe string for job_key for logging/DB calls
            if job_key:
                job_key_str = str(job_key)
            else:
                job_key_str = f'unknown_{int(time.time())}'

            xyz_path = job_payload.get('xyz_path') or job_payload.get('xyz_file')
            optimization = job_payload.get('optimization_level', 'normal')

            logger.info('Processing job %s (msg_id=%s)', job_key_str, msg_id)

            try:
                # If an xyz_path is provided that is a path relative to JOBS_DIR, ensure full path
                if xyz_path and self.xtb_cfg is not None:
                    if not os.path.isabs(xyz_path):
                        xyz_path_full = os.path.join(self.xtb_cfg.JOBS_DIR, xyz_path)
                    else:
                        xyz_path_full = xyz_path
                else:
                    xyz_path_full = None

                # Execute xTB (in threadpool to avoid blocking event loop)
                if not self.xtb_runner or not xyz_path_full:
                    # Fallback: mark as failed in DB if possible, or log
                    logger.warning('XTBRunner or xyz path not available for job %s', job_key_str)
                    return

                loop = asyncio.get_running_loop()
                # Ensure we call execute with definite string args
                job_key_for_exec = job_key_str
                func = functools.partial(self.xtb_runner.execute, str(xyz_path_full), job_key_for_exec, optimization)
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func),
                    timeout=self.cfg.job_timeout,
                )

                # Persist results: attempt to save into JobStore (filesystem) if available
                if self.job_store:
                    try:
                        self.job_store.save_results(job_key_str, result)
                    except Exception as e:
                        logger.error('Failed to save results to JobStore for %s: %s', job_key_str, e)

                # Update jobs table via SupabaseJobStore if available
                try:
                    if self.supabase_store:
                        self.supabase_store.save_results(job_key_str, {'result_summary': {'energy': result.get('energy')}})
                except Exception as e:
                    logger.debug('Could not update jobs table for %s: %s', job_key_str, e)

                logger.info('\u2713 Job %s completed (energy=%s)', job_key, result.get('energy'))

            except asyncio.TimeoutError:
                logger.error('Job %s timed out after %ss', job_key, self.cfg.job_timeout)
                try:
                    if self.supabase_store and job_key_str:
                        self.supabase_store.update_job_status(job_key_str, 'failed')
                except Exception:
                    pass
            except Exception as e:
                logger.error('Unexpected error processing job %s: %s', job_key, e)
                logger.debug(traceback.format_exc())
                try:
                    if self.supabase_store and job_key_str:
                        self.supabase_store.update_job_status(job_key_str, 'failed')
                except Exception:
                    pass

    async def run_pgmq_loop(self):
        logger.info('Starting PGMQ worker loop (queue=%s)', self.cfg.queue_name)
        self.running = True

        while self.running:
            try:
                rows = self.read_pgmq_batch()
                if not rows:
                    await asyncio.sleep(self.cfg.poll_interval)
                    continue

                tasks = []
                for r in rows:
                    # r is a dict from RealDictCursor; try common column names
                    msg_id = r.get('id') or r.get('message_id') or r.get('msg_id')
                    payload = r.get('payload') or r.get('data') or r.get('message')
                    # payload may be JSON string or dict
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            logger.warning('Message payload not JSON: %s', payload)
                            payload = {'raw': payload}
                    # Ensure payload is a dict for typing and downstream processing
                    if payload is None or not isinstance(payload, dict):
                        payload = {'raw': payload}

                    # spawn async tasks
                    tasks.append(asyncio.create_task(self._process_job_from_payload(payload, msg_id)))

                    # archive message after scheduling (best-effort)
                    if msg_id is not None:
                        try:
                            self.archive_pgmq(msg_id)
                        except Exception as e:
                            logger.debug('Failed to archive msg %s: %s', msg_id, e)

                # wait for tasks (but do not block forever)
                if tasks:
                    await asyncio.gather(*tasks)

            except Exception as e:
                logger.error('Error in PGMQ loop: %s', e)
                logger.debug(traceback.format_exc())
                await asyncio.sleep(self.cfg.poll_interval)

    async def run_filesystem_fallback(self):
        """Simple fallback: poll filesystem job store for queued jobs and process them.
        This uses the existing JobStore and mirrors semantics of the prior worker.
        """
        logger.info('PGMQ not available; using filesystem fallback')
        if not self.job_store:
            raise RuntimeError('JobStore is not available')

        while self.running:
            try:
                queued = self.job_store.list_jobs(status='QUEUED', limit=10)
                for meta in queued:
                    job_id = meta.get('job_id')
                    if not job_id:
                        continue
                    # schedule processing using _process_job_from_payload
                    payload = {'job_key': job_id, 'xyz_file': meta.get('xyz_file'), 'optimization_level': meta.get('optimization_level', 'normal')}
                    await self._process_job_from_payload(payload, msg_id=None)
                await asyncio.sleep(self.cfg.poll_interval)
            except Exception as e:
                logger.error('Filesystem fallback error: %s', e)
                logger.debug(traceback.format_exc())
                await asyncio.sleep(self.cfg.poll_interval)

    async def run(self):
        try:
            self.connect_db()
        except Exception as e:
            logger.error('Database connection failed: %s', e)
            # If DB is not available, fallback to filesystem if possible
            if self.job_store:
                self.running = True
                await self.run_filesystem_fallback()
            return

        try:
            if self.pgmq_available():
                await self.run_pgmq_loop()
            else:
                await self.run_filesystem_fallback()
        except KeyboardInterrupt:
            logger.info('Interrupted, shutting down')
        finally:
            self.running = False
            try:
                if self.supabase_store:
                    try:
                        self.supabase_store.close()
                    except Exception:
                        pass
            except Exception:
                pass


if __name__ == '__main__':
    cfg = PGMQWorkerConfig()
    worker = PGMQWorker(cfg)
    try:
        asyncio.run(worker.run())
    except Exception as e:
        logger.error('Worker crashed: %s', e)
        logger.debug(traceback.format_exc())
        raise
