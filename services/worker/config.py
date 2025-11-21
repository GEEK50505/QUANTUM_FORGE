"""
Configuration module for Quantum Forge Worker.

Handles environment variables, Supavisor connection pooling setup, and
centralized configuration following the 12-Factor App principle.

Key responsibility: Parse and validate the Supavisor connection string,
ensuring IPv4 connectivity even in environments without IPv6 routing.
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WorkerConfig:
    """
    Centralized configuration for the Quantum Forge worker.
    
    Attributes:
        db_pooler_string: PostgreSQL connection string pointing to Supavisor
                         (AWS IPv4 pooler endpoint, Session Mode port 5432).
        supabase_url: Supabase project URL (for Storage API).
        supabase_key: Supabase Service Role Key (for authenticated Storage access).
        worker_queue: Name of the queue table (default: 'xtb_job_queue').
        poll_interval: Seconds to wait between job polling cycles.
        job_timeout: Hard timeout in seconds for job execution.
        log_level: Logging verbosity level.
        log_bucket: Supabase Storage bucket for logs.
    """
    
    def __init__(self):
        # Database configuration - CRITICAL: must use Supavisor pooler, not direct host
        self.db_pooler_string = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres.token:password@aws-0-region.pooler.supabase.com:5432/postgres'
        )
        
        # Validate that we're using the pooler, not direct Supabase
        self._validate_pooler_dsn()
        
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://project.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        
        # Worker behavior
        self.worker_queue = os.getenv('WORKER_QUEUE', 'xtb_job_queue')
        self.poll_interval = float(os.getenv('WORKER_POLL_INTERVAL', '2.0'))
        self.job_timeout = int(os.getenv('JOB_TIMEOUT', '3600'))  # 1 hour default
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_bucket = os.getenv('LOG_BUCKET', 'job_artifacts')
        
        # Buffer configuration for async logging
        self.log_buffer_size = int(os.getenv('LOG_BUFFER_SIZE', '50'))  # lines
        self.log_flush_interval = int(os.getenv('LOG_FLUSH_INTERVAL', '10'))  # seconds
        self.log_queue_maxsize = int(os.getenv('LOG_QUEUE_MAXSIZE', '5000'))  # max items
    
    def _validate_pooler_dsn(self):
        """
        Validate that the DATABASE_URL points to the Supavisor pooler.
        
        Raises a warning if using the direct Supabase host (IPv6-only),
        which will fail in IPv4-only environments like GitHub Actions.
        """
        try:
            parsed = urlparse(self.db_pooler_string)
            hostname = parsed.hostname or ''
            
            # Direct Supabase hosts are in the form: db.<project>.supabase.co
            # Pooler hosts are in the form: aws-0-<region>.pooler.supabase.com
            if hostname.endswith('.supabase.co') and '.pooler.' not in hostname:
                logger.error(
                    f"CRITICAL: DATABASE_URL appears to use direct Supabase host '{hostname}'. "
                    f"This will fail in IPv4-only environments (GitHub Actions, Render, etc.) "
                    f"because the direct host resolves to IPv6-only addresses. "
                    f"Use Supavisor (Session Mode): "
                    f"'postgres://user.project:password@aws-0-region.pooler.supabase.com:5432/postgres'"
                )
            
            # Check for Session Mode (port 5432) vs Transaction Mode (port 6543)
            if parsed.port == 6543:
                logger.warning(
                    f"Database port is 6543 (Transaction Mode). "
                    f"This mode does not support prepared statements (used by psycopg2 by default). "
                    f"Use port 5432 (Session Mode) for long-running workers."
                )
            
            logger.info(f"Database pooler host: {hostname}:{parsed.port}")
        
        except Exception as e:
            logger.warning(f"Could not validate DATABASE_URL format: {e}")
    
    def get_db_connection_params(self) -> dict:
        """
        Return connection parameters for psycopg2.connect().
        
        Ensures:
        - sslmode='require' for encrypted connections.
        - connect_timeout for early failure detection.
        - application_name for server-side logging/monitoring.
        
        Returns:
            Dictionary of psycopg2 connection parameters.
        """
        parsed = urlparse(self.db_pooler_string)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') or 'postgres',
            'sslmode': 'require',  # CRITICAL: enforce TLS
            'connect_timeout': 5,  # fail fast on unreachable pooler
            'application_name': 'quantum_worker',
        }
    
    def to_dict(self) -> dict:
        """Return a dict representation (for logging; omits secrets)."""
        return {
            'db_pooler_string': '***' + (self.db_pooler_string or '')[-30:],
            'supabase_url': self.supabase_url,
            'worker_queue': self.worker_queue,
            'poll_interval': self.poll_interval,
            'job_timeout': self.job_timeout,
            'log_level': self.log_level,
            'log_buffer_size': self.log_buffer_size,
            'log_flush_interval': self.log_flush_interval,
        }


# Singleton configuration instance
config = WorkerConfig()
