"""
Enqueue Job API Script

Demonstrates transactional job enqueueing using SupabaseJobStore.
This can be called from the frontend or as a standalone script.

Usage (standalone):
  . .venv/bin/activate
  export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
  python backend/api/enqueue_job.py --job-key test_job_001 --xyz-file jobs/test_job_001/water.xyz

Usage (from backend API):
  from backend.api.enqueue_job import enqueue_job_api
  job_key = enqueue_job_api(
      job_key='my_job',
      payload={'xyz_file': 'path/to/water.xyz', 'optimization_level': 'normal'},
      user_id='user-uuid-here'
  )

"""
import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.supabase_job_store import SupabaseJobStore


def enqueue_job_api(job_key: str, payload: dict, user_id: str = None) -> str:
    """
    Enqueue a job transactionally into Supabase.

    Args:
        job_key: Unique identifier for the job
        payload: Job payload (should include xyz_file, optimization_level, etc.)
        user_id: Optional user UUID

    Returns:
        job_key on success

    Raises:
        RuntimeError if DATABASE_URL not set or transaction fails
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL environment variable not set')

    store = SupabaseJobStore(database_url)
    store.connect()
    try:
        result = store.enqueue_job_transactional(job_key, payload, user_id)
        return result
    finally:
        store.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enqueue a job for xTB calculation')
    parser.add_argument('--job-key', required=True, help='Unique job identifier')
    parser.add_argument('--xyz-file', required=True, help='Path to XYZ file relative to jobs directory')
    parser.add_argument('--optimization-level', default='normal', choices=['normal', 'tight'], help='xTB optimization level')
    parser.add_argument('--user-id', default=None, help='Optional user UUID')
    args = parser.parse_args()

    payload = {
        'job_key': args.job_key,
        'xyz_file': args.xyz_file,
        'optimization_level': args.optimization_level,
    }

    try:
        result = enqueue_job_api(args.job_key, payload, user_id=args.user_id)
        print(f'✓ Job {result} enqueued successfully')
    except Exception as e:
        print(f'✗ Failed to enqueue job: {e}', file=sys.stderr)
        sys.exit(1)
