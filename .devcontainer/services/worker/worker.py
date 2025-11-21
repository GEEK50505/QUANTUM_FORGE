"""Production-ready worker for QUANTUM_FORGE.

Features:
- Polls a pgmq queue (`xtb_job_queue`) via direct DB calls.
- Falls back to SELECT ... FOR UPDATE SKIP LOCKED if pgmq not available.
- Instantiates strategies from `strategies.py` (currently XTBStrategy).
- Streams logs via `LogSyncer` to Supabase Storage `job_artifacts` bucket.

Usage: set `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` (for storage uploads).
Run: `python services/worker/worker.py`
"""
import os
import time
import json
import tempfile
import traceback
import logging
from typing import Optional
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras

from strategies import XTBStrategy, ComputeStrategy
from logger import LogSyncer

QUEUE_NAME = os.getenv('WORKER_QUEUE', 'xtb_job_queue')
POLL_INTERVAL = float(os.getenv('WORKER_POLL_INTERVAL', '1.0'))
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BUCKET = os.getenv('WORKER_BUCKET', 'job_artifacts')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('worker')
logger.setLevel(logging.DEBUG)


# Logging cursor wrappers to capture SQL and params for diagnostics
try:
    from psycopg2.extras import RealDictCursor as _RealDictCursor
except Exception:
    _RealDictCursor = None

from psycopg2.extensions import cursor as _BaseCursor
from psycopg2 import extensions as _pg_ext


class LoggingCursor(_BaseCursor):
    def execute(self, query, vars=None):
        try:
            print('SQL Execute:', query, 'params=', vars)
            logger.debug('SQL Execute: %s | params=%r', query, vars)
            return super().execute(query, vars)
        except Exception as e:
            print('SQL failed:', query, 'params=', vars, 'error=', e)
            logger.exception('SQL failed: %s | params=%r | error=%s', query, vars, e)
            try:
                logger.debug('Cursor.query: %s', getattr(self, 'query', None))
            except Exception:
                pass
            raise


class LoggingRealDictCursor(_RealDictCursor if _RealDictCursor is not None else _BaseCursor):
    def execute(self, query, vars=None):
        try:
            print('SQL Execute (RealDictCursor):', query, 'params=', vars)
            logger.debug('SQL Execute (RealDictCursor): %s | params=%r', query, vars)
            return super().execute(query, vars)
        except Exception as e:
            print('SQL failed (RealDictCursor):', query, 'params=', vars, 'error=', e)
            logger.exception('SQL failed (RealDictCursor): %s | params=%r | error=%s', query, vars, e)
            try:
                logger.debug('Cursor.query: %s', getattr(self, 'query', None))
            except Exception:
                pass
            raise


def connect_db(dsn: str):
    conn = psycopg2.connect(dsn)
    conn.autocommit = False

    # Wrap the connection.cursor to default to logging cursors when no factory provided
    orig_cursor = conn.cursor

    def cursor_wrapper(*args, **kwargs):
        cf = kwargs.get('cursor_factory')
        print('cursor_wrapper called; args=', args, 'kwargs=', kwargs)
        logger.debug('cursor_wrapper called; args=%r kwargs=%r', args, kwargs)
        if cf is None:
            # default to LoggingCursor
            return orig_cursor(cursor_factory=LoggingCursor)
        # map RealDictCursor to our LoggingRealDictCursor
        try:
            import psycopg2.extras as _pge
            if cf is _pge.RealDictCursor:
                kwargs['cursor_factory'] = LoggingRealDictCursor
        except Exception:
            pass
        return orig_cursor(*args, **kwargs)

    conn.cursor = cursor_wrapper
    return conn


def conn_in_error_state(conn) -> bool:
    try:
        return conn.get_transaction_status() == _pg_ext.TRANSACTION_STATUS_INERROR
    except Exception:
        return True


def safe_reconnect(dsn: str, conn):
    """Attempt to rollback and reconnect if the connection is unusable.

    Returns a fresh connection or raises the last exception.
    """
    try:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                # close and drop to force reconnect
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
    except Exception:
        conn = None

    if conn is None:
        # try to create a fresh connection
        return connect_db(dsn)
    return conn


def _warn_if_direct_supabase(dsn: str):
    """Warn users if they are using the Supabase direct host (IPv6-only) instead of the pooler.

    If the DSN hostname ends with `.supabase.co` (direct DB) advise switching to the
    connection pooling (session mode) pooler host which supports IPv4.
    """
    if not dsn:
        return
    try:
        parsed = urlparse(dsn if '://' in dsn else f'postgresql://{dsn}')
        hostname = parsed.hostname or ''
        # Direct Supabase DB hostname commonly ends with `.supabase.co`
        if hostname.endswith('.supabase.co') and '.pooler.' not in hostname:
            logger.warning(
                "Detected Supabase direct DB host '%s'. If you see connection timeouts or 'Network is unreachable',\n"
                "please use the Supavisor connection pooler (Session Mode) URL from the Supabase dashboard.\n"
                "Example: connect to a host like '<project>.pooler.supabase.com' on port 5432 instead of the direct host.\n"
                "This environment (or Docker) often lacks IPv6 routing and the direct host resolves to IPv6-only addresses.",
                hostname,
            )
    except Exception:
        # non-fatal; don't raise from a helper warning routine
        return


def pgmq_read(conn, queue_name: str, vt_seconds: int = 60) -> Optional[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        try:
            # Try different pgmq.read signatures based on version
            try:
                cur.execute('SELECT * FROM pgmq.read(%s, %s, 1)', (queue_name, vt_seconds))
            except psycopg2.Error:
                # Fallback to older signature
                cur.execute('SELECT * FROM pgmq.read(%s, %s)', (queue_name, vt_seconds))
            row = cur.fetchone()
            if row:
                return dict(row)
        except psycopg2.Error as e:
            # some pgmq versions or missing extension will error; caller should fallback
            logger.exception('pgmq.read() raised an exception: %s, pgcode: %s, pgerror: %s', 
                           type(e).__name__, getattr(e, 'pgcode', None), getattr(e, 'pgerror', None))
            try:
                conn.rollback()
            except Exception:
                logger.exception('conn.rollback() after pgmq.read() failure failed')
            return None
        except Exception as e:
            logger.exception('pgmq.read() raised unexpected exception: %s', type(e).__name__)
            try:
                conn.rollback()
            except Exception:
                logger.exception('conn.rollback() after pgmq.read() failure failed')
            return None
    return None


def claim_job_skip_locked(conn) -> Optional[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        try:
            cur.execute("BEGIN")
        except Exception as e:
            logger.exception('BEGIN failed in claim_job_skip_locked: %s', e)
            try:
                conn.rollback()
            except Exception:
                logger.exception('rollback after BEGIN failure also failed')
            raise
        cur.execute(
            "SELECT id, payload, user_id FROM public.jobs WHERE status = 'queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1",
        )
        row = cur.fetchone()
        if not row:
            cur.execute("ROLLBACK")
            return None
        job_id = row['id']
        cur.execute("UPDATE public.jobs SET status = 'processing', started_at = now() WHERE id = %s", (job_id,))
        conn.commit()
        return dict(row)


def update_job(conn, job_id: str, status: str, result: Optional[dict] = None, log_url: Optional[str] = None, error: Optional[str] = None):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE public.jobs SET status = %s, result = %s, log_url = %s, error_message = %s, finished_at = CASE WHEN %s = 'completed' THEN now() ELSE finished_at END WHERE id = %s",
            (status, json.dumps(result) if result is not None else None, log_url, error, status, job_id),
        )
        conn.commit()


def ack_pgmq_message(conn, msg_row: dict):
    # Try to acknowledge/remove the message from the queue
    try:
        msg_id = None
        # pgmq.read may return numeric id column or 'id'
        if 'id' in msg_row:
            msg_id = msg_row['id']
        elif 'msg_id' in msg_row:
            msg_id = msg_row['msg_id']

        if msg_id is not None:
            with conn.cursor() as cur:
                cur.execute('SELECT pgmq.ack(%s)', (msg_id,))
                conn.commit()
    except Exception:
        # best-effort; ignore ack failures
        logger.exception('pgmq ack failed')


def load_strategy(payload: dict) -> ComputeStrategy:
    # Choose strategy by payload contents; default to XTB
    return XTBStrategy()


def process_message(conn, msg_row: dict):
    # msg_row may be from pgmq.read or from SKIP_LOCKED job row
    job_id = msg_row.get('job_id') or msg_row.get('id')
    payload = msg_row.get('payload') or msg_row.get('body') or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    user_id = msg_row.get('user_id')

    # claim / mark processing already handled upstream for SKIP_LOCKED path

    # Prepare workdir and log file
    with tempfile.TemporaryDirectory(prefix=f'job_{job_id}_') as workdir:
        log_local = os.path.join(workdir, 'run.log')

        # create empty log file
        open(log_local, 'wb').close()

        remote_path = f"{user_id}/{job_id}/run.log"
        syncer = LogSyncer(log_local, SUPABASE_URL, SUPABASE_KEY, BUCKET, remote_path)
        syncer.start()

        # write helper to append bytes to log
        def log_writer(chunk: bytes):
            try:
                with open(log_local, 'ab') as f:
                    f.write(chunk)
            except Exception:
                pass

        strategy = load_strategy(payload)
        try:
            result = strategy.run(payload, workdir, log_writer)
            # Final upload/stop
            syncer.stop_and_finish()

            # Update DB
            if job_id:
                update_job(conn, job_id, 'completed', result, f"/storage/v1/object/public/{BUCKET}/{remote_path}")
                # ack if message from pgmq
                ack_pgmq_message(conn, msg_row)
        except Exception as e:
            syncer.stop_and_finish()
            tb = traceback.format_exc()
            logger.error('Job %s failed: %s', job_id, tb)
            if job_id:
                update_job(conn, job_id, 'failed', None, None, str(e))
                # try to ack/archive the message so it doesn't loop forever
                ack_pgmq_message(conn, msg_row)


def run_loop(dsn: str):
    if not dsn:
        raise RuntimeError('DATABASE_URL must be set')
    # Warn if user provided a direct Supabase host (IPv6-only)
    try:
        _warn_if_direct_supabase(dsn)
    except Exception:
        pass
    conn = None
    try:
        while True:
            # Ensure we have a healthy connection
            if conn is None:
                try:
                    conn = connect_db(dsn)
                    logger.info('Connected to DB; starting worker loop')
                except Exception:
                    logger.exception('Failed to connect to DB; retrying')
                    time.sleep(POLL_INTERVAL)
                    continue

            # If the connection has an in-error transaction, attempt a safe reconnect
            try:
                if conn_in_error_state(conn):
                    logger.warning('Connection in error state; attempting reconnect')
                    try:
                        conn = safe_reconnect(dsn, conn)
                        logger.info('Reconnected to DB after error state')
                    except Exception:
                        logger.exception('Reconnect attempt failed; will retry')
                        conn = None
                        time.sleep(POLL_INTERVAL)
                        continue

            except Exception:
                # If checking status itself fails, replace the connection
                logger.exception('Failed to inspect connection state; reconnecting')
                try:
                    if conn is not None:
                        conn.close()
                except Exception:
                    pass
                conn = None
                time.sleep(POLL_INTERVAL)
                continue

            try:
                msg = None
                # Try pgmq.read first
                try:
                    msg = pgmq_read(conn, QUEUE_NAME, vt_seconds=60)
                except Exception:
                    # Log and continue to fallback
                    logger.exception('pgmq_read failed; falling back to SKIP LOCKED')
                    msg = None

                if not msg:
                    # fallback to skip-locked claim
                    # ensure any previous aborted transaction state is cleared
                    try:
                        conn.rollback()
                    except Exception:
                        logger.debug('No rollback needed or rollback failed when clearing state')
                    try:
                        msg = claim_job_skip_locked(conn)
                    except Exception:
                        logger.exception('claim_job_skip_locked failed')
                        # rollback any aborted transaction and continue
                        try:
                            conn.rollback()
                        except Exception:
                            logger.exception('rollback after claim_job failure also failed')
                        time.sleep(POLL_INTERVAL)
                        continue

                if msg:
                    try:
                        process_message(conn, msg)
                    except Exception:
                        # ensure we rollback if processing left transaction in bad state
                        logger.exception('process_message raised an exception')
                        try:
                            conn.rollback()
                        except Exception:
                            logger.exception('rollback after process_message failed')
                    continue

                time.sleep(POLL_INTERVAL)
            except Exception:
                # Catch any unexpected error in the loop, log full traceback and rollback
                logger.exception('Unexpected error in worker loop; rolling back and retrying')
                try:
                    conn.rollback()
                except Exception:
                    logger.exception('rollback failed after unexpected error')
                time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info('Worker interrupted, exiting')
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    if args.dry_run:
        print('Dry-run: environment variables needed: DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY')
    else:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print('DATABASE_URL not set; cannot run worker in non-dry mode.')
            exit(2)
        try:
            _warn_if_direct_supabase(DATABASE_URL)
        except Exception:
            pass
        run_loop(DATABASE_URL)
