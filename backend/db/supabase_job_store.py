"""SupabaseJobStore adapter

Provides a thin adapter over Postgres/Supabase for enqueueing jobs via pgmq
and for fallback queueing via `FOR UPDATE SKIP LOCKED`.

This implementation uses psycopg2 (blocking). The worker runs these calls
in the threadpool to avoid blocking the event loop.
"""
import json
import logging
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger('supabase_job_store')


class SupabaseJobStore:
    def __init__(self, database_url: str, queue_name: str = 'xtb_calculation_queue'):
        self.database_url = database_url
        self.queue_name = queue_name
        self.conn: Optional[psycopg2.extensions.connection] = None

    def connect(self):
        if not self.database_url:
            raise RuntimeError('DATABASE_URL not provided')
        self.conn = psycopg2.connect(self.database_url)
        # Use DictCursor for convenience
        logger.info('SupabaseJobStore connected')

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

    def pgmq_available(self) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pgmq'")
                return bool(cur.fetchone())
        except Exception as e:
            logger.debug('pgmq availability check failed: %s', e)
            return False

    def send_pgmq(self, payload: Dict[str, Any]) -> Any:
        """Send payload to pgmq queue. Returns whatever pgmq.send returns (often a message id)."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT pgmq.send(%s, %s::jsonb);", (self.queue_name, json.dumps(payload)))
                res = cur.fetchone()
                self.conn.commit()
                return res[0] if res else None
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('pgmq.send failed: %s', e)
            raise

    def read_pgmq(self, batch_size: int, visibility_timeout: int) -> List[Dict[str, Any]]:
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Note: some pgmq versions accept (queue, vt, n)
                cur.execute('SELECT * FROM pgmq.read(%s, %s, %s);', (self.queue_name, visibility_timeout, batch_size))
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.debug('read_pgmq failed: %s', e)
            return []

    def archive_pgmq(self, msg_id: Any):
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT pgmq.archive(%s);', (msg_id,))
                self.conn.commit()
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('pgmq.archive failed: %s', e)

    def enqueue_job_transactional(self, job_key: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
        """Insert into public.jobs and pgmq.send in same transaction.
        Returns job_key on success.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute('BEGIN;')
                cur.execute('INSERT INTO public.jobs (job_key, user_id, status, payload) VALUES (%s, %s, %s, %s) RETURNING id;', (job_key, user_id, 'queued', json.dumps(payload)))
                cur.execute("SELECT pgmq.send(%s, %s::jsonb);", (self.queue_name, json.dumps(payload)))
                cur.execute('COMMIT;')
                return job_key
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('enqueue_job_transactional failed: %s', e)
            raise

    def fetch_and_lock_queued(self, limit: int = 1) -> List[Dict[str, Any]]:
        """Fetch queued jobs using SELECT ... FOR UPDATE SKIP LOCKED (fallback when pgmq not available).
        Returns list of jobs with keys: id, job_key, payload
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("BEGIN;")
                cur.execute("SELECT id, job_key, payload FROM public.jobs WHERE status = 'queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT %s;", (limit,))
                rows = cur.fetchall()
                job_keys = [r['job_key'] for r in rows]
                if job_keys:
                    cur.execute("UPDATE public.jobs SET status = 'running', updated_at = now() WHERE job_key = ANY(%s);", (job_keys,))
                cur.execute('COMMIT;')
                return [dict(r) for r in rows]
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('fetch_and_lock_queued failed: %s', e)
            return []

    def update_job_status(self, job_key: str, status: str, extra: Optional[Dict[str, Any]] = None):
        try:
            with self.conn.cursor() as cur:
                if extra:
                    cur.execute("UPDATE public.jobs SET status = %s, payload = COALESCE(payload, '{}'::jsonb) || %s::jsonb, updated_at = now() WHERE job_key = %s", (status, json.dumps(extra), job_key))
                else:
                    cur.execute("UPDATE public.jobs SET status = %s, updated_at = now() WHERE job_key = %s", (status, job_key))
                self.conn.commit()
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('update_job_status failed for %s: %s', job_key, e)

    def save_results(self, job_key: str, result: Dict[str, Any]):
        try:
            with self.conn.cursor() as cur:
                cur.execute("UPDATE public.jobs SET status = %s, payload = COALESCE(payload, '{}'::jsonb) || %s::jsonb, updated_at = now() WHERE job_key = %s", ('completed', json.dumps({'result': result}), job_key))
                self.conn.commit()
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.error('save_results failed for %s: %s', job_key, e)
