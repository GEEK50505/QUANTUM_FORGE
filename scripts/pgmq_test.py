#!/usr/bin/env python3
"""
Test harness for PGMQ + worker integration.

1. Runs the migration SQL (idempotent)
2. Creates a test job in `jobs` directory and writes an XYZ file
3. Transactionally inserts a row into `public.jobs` and calls `pgmq.send` to enqueue
4. Starts the `PGMQWorker` (from services/worker/pgmq_worker.py) and waits for completion

Usage:
  . .venv/bin/activate
  export DATABASE_URL=postgresql://user:pass@host:5432/dbname
  python scripts/pgmq_test.py

"""
import os
import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION = REPO_ROOT / 'deploy' / 'migrations' / '20251121_001_create_pgmq_and_jobs_updatedv2.sql'

# Ensure repo root is importable
sys.path.insert(0, str(REPO_ROOT))

try:
    from backend.config import XTBConfig
    from services.worker.pgmq_worker import PGMQWorker, PGMQWorkerConfig
except Exception as e:
    print('Failed to import project modules:', e)
    raise

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('ERROR: DATABASE_URL must be set in environment')
    sys.exit(1)

JOB_XYZ = """3
Water
O 0 0 0
H 0 0 0
H 0 0 0
"""


def apply_migration(conn):
    print('Applying migration (idempotent)')
    sql = MIGRATION.read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print('Migration applied')


def create_job_files(cfg, job_key):
    jobs_dir = Path(cfg.JOBS_DIR)
    p = jobs_dir / job_key
    p.mkdir(parents=True, exist_ok=True)
    xyz_path = p / 'water.xyz'
    xyz_path.write_text(JOB_XYZ)
    return str(xyz_path.relative_to(jobs_dir))


async def run_test():
    cfg = XTBConfig()
    # Connect to Postgres
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    try:
        apply_migration(conn)

        job_key = f'test_pgmq_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}'
        xyz_rel = create_job_files(cfg, job_key)
        payload = {
            'job_key': job_key,
            'xyz_file': f'{job_key}/water.xyz',
            'optimization_level': 'normal'
        }

        # Transactionally insert job row and send pgmq message
        with conn.cursor() as cur:
            print('Beginning transactional enqueue')
            cur.execute('BEGIN;')
            cur.execute('INSERT INTO public.jobs (job_key, user_id, status, payload) VALUES (%s, %s, %s, %s) RETURNING id', (job_key, None, 'queued', json.dumps(payload)))
            cur.execute("SELECT pgmq.send(%s, %s::jsonb);", ('xtb_calculation_queue', json.dumps(payload)))
            cur.execute('COMMIT;')
            print('Enqueued job', job_key)

    except Exception as e:
        print('Error during enqueue:', e)
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()

    # Start the worker in-process and watch for job completion
    worker_cfg = PGMQWorkerConfig()
    worker = PGMQWorker(worker_cfg)

    async def _run_worker():
        await worker.run()

    # Run worker as background task
    loop = asyncio.get_running_loop()
    worker_task = loop.create_task(_run_worker())

    # Poll jobs table for status change
    watch_conn = psycopg2.connect(DATABASE_URL)
    watch_conn.autocommit = True
    try:
        with watch_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            start = time.time()
            timeout = 120
            while True:
                cur.execute('SELECT status, payload FROM public.jobs WHERE job_key = %s', (job_key,))
                row = cur.fetchone()
                if row:
                    status = row['status']
                    print('Job status:', status)
                    if status.lower() == 'completed' or status.lower() == 'finished':
                        print('Job completed')
                        break
                    if status.lower() == 'failed':
                        print('Job failed')
                        break
                if time.time() - start > timeout:
                    print('Timeout waiting for job completion')
                    break
                await asyncio.sleep(2)
    finally:
        # Stop worker
        worker.running = False
        await asyncio.sleep(1)
        try:
            if not worker_task.done():
                worker_task.cancel()
        except Exception:
            pass
        watch_conn.close()


if __name__ == '__main__':
    asyncio.run(run_test())
