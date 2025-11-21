"""
Buffered logging module for Quantum Forge Worker.

Implements the Producer-Consumer pattern to decouple log generation from
remote persistence. The main thread logs to a queue; a background thread
batches and uploads logs to Supabase Storage.

Key design:
- Main thread: logger.info() → emit() → Queue.put() (< 1ms, non-blocking)
- Background thread: accumulate logs, upload when buffer fills or time expires
- Graceful shutdown: atexit handler flushes remaining logs before exit
"""

import logging
import queue
import threading
import atexit
import time
from datetime import datetime
from typing import Optional
import json
import uuid

from config import config

logger = logging.getLogger(__name__)


class SupabaseStorageHandler(logging.Handler):
    """
    A custom logging handler that queues log records for asynchronous
    dispatch to Supabase Storage.
    
    Design rationale:
    - emit() does NOT make network calls; it pushes to a thread-safe queue.
    - This ensures the main thread is never blocked by HTTP latency.
    - The background LogConsumer thread handles actual uploads.
    """
    
    def __init__(self, log_queue: 'queue.Queue'):
        super().__init__()
        self.log_queue = log_queue
        self.formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Format the log record and push it to the queue.
        
        If the queue is full (unlikely under normal conditions), we log a warning
        and drop the record rather than blocking the main thread.
        """
        try:
            msg = self.format(record)
            # Try to put the message in the queue without blocking.
            # If the queue is full, drop the log (safer than blocking).
            self.log_queue.put_nowait(msg)
        except queue.Full:
            # Queue is full; log dropped. This indicates the consumer is
            # severely behind. Log a warning to stderr directly.
            print(f"WARNING: Log queue full, dropping message: {record.getMessage()}")
        except Exception as e:
            # Fallback: print to stderr if something goes wrong with the queue.
            print(f"ERROR in SupabaseStorageHandler.emit: {e}")


class LogConsumer(threading.Thread):
    """
    Background thread that consumes log records from the queue and
    batches them to Supabase Storage.
    
    Design:
    - Runs as a daemon thread (exits when main program exits).
    - Accumulates logs until size or time threshold is reached.
    - Uploads in a single HTTP request (batched) to Supabase Storage.
    - Handles shutdown gracefully via a sentinel value (None).
    """
    
    def __init__(self, log_queue: 'queue.Queue', job_id: str, user_id: Optional[str] = None):
        super().__init__(daemon=True, name='LogConsumer')
        self.log_queue = log_queue
        self.job_id = job_id
        self.user_id = user_id or 'unknown'
        self.buffer: list[str] = []
        self.last_flush_time = time.time()
        self.running = True
        self.supabase_client = None
        
        # Initialize Supabase client (lazy; only if we actually upload logs)
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize the Supabase client for Storage operations."""
        try:
            from supabase import create_client
            self.supabase_client = create_client(
                config.supabase_url,
                config.supabase_key
            )
            logger.debug(f"Supabase client initialized for bucket '{config.log_bucket}'")
        except ImportError:
            logger.warning("supabase-py not installed; logging to Supabase Storage disabled")
            self.supabase_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase_client = None
    
    def run(self):
        """
        Main loop: consume logs from queue and upload when thresholds are reached.
        
        Loop exits when it receives a None (sentinel) value, indicating shutdown.
        """
        logger.debug(f"LogConsumer started for job {self.job_id}")
        
        try:
            while self.running:
                try:
                    # Blocking get with timeout to allow periodic flush checks.
                    # Timeout is smaller than flush_interval to ensure timely flushes.
                    timeout = config.log_flush_interval - (time.time() - self.last_flush_time)
                    timeout = max(1, min(timeout, 5))  # clamp to 1-5 seconds
                    
                    msg = self.log_queue.get(timeout=timeout)
                    
                    # Check for sentinel value (None) indicating shutdown.
                    if msg is None:
                        logger.debug("LogConsumer received shutdown sentinel")
                        self.running = False
                        break
                    
                    # Add the message to the buffer.
                    self.buffer.append(msg)
                    
                    # Check if we should flush (size threshold).
                    if len(self.buffer) >= config.log_buffer_size:
                        self._flush_logs()
                
                except queue.Empty:
                    # Timeout waiting for next log; check if time threshold is reached.
                    if time.time() - self.last_flush_time >= config.log_flush_interval:
                        if self.buffer:
                            self._flush_logs()
        
        finally:
            # On exit (normal or exception), ensure any buffered logs are flushed.
            if self.buffer:
                logger.info(f"LogConsumer exiting; flushing {len(self.buffer)} buffered logs")
                self._flush_logs()
    
    def _flush_logs(self):
        """
        Upload the accumulated logs to Supabase Storage.
        
        Naming convention: logs/{user_id}/{job_id}/{timestamp}_{batch_id}.log
        This prevents collisions and allows easy grouping by job and user.
        """
        if not self.buffer:
            return
        
        timestamp = datetime.utcnow().isoformat()
        batch_id = str(uuid.uuid4())[:8]
        
        # Construct the file path in Supabase Storage.
        file_path = f"{self.user_id}/{self.job_id}/{timestamp}_{batch_id}.log"
        
        # Join all buffered logs into a single file content.
        file_content = '\n'.join(self.buffer) + '\n'
        
        logger.debug(f"Flushing {len(self.buffer)} log lines to {config.log_bucket}/{file_path}")
        
        if self.supabase_client:
            try:
                # Upload to Supabase Storage.
                # The file_content is bytes, so encode if necessary.
                response = self.supabase_client.storage \
                    .from_(config.log_bucket) \
                    .upload(
                        file_path,
                        file_content.encode('utf-8'),
                        {
                            'content-type': 'text/plain',
                            'upsert': 'false',  # Don't overwrite if exists
                        }
                    )
                
                logger.info(f"Uploaded {len(self.buffer)} logs to {file_path}")
            except Exception as e:
                logger.error(f"Failed to upload logs to Supabase Storage: {e}")
                # Don't crash the consumer; just warn and continue.
        else:
            # Supabase client unavailable; fall back to local logging.
            logger.warning(f"Supabase client unavailable; {len(self.buffer)} logs not persisted remotely")
        
        # Clear the buffer and reset the flush timer.
        self.buffer.clear()
        self.last_flush_time = time.time()


class BufferedLogger:
    """
    Facade for setting up buffered logging.
    
    Usage:
        log_mgr = BufferedLogger(job_id='job_123', user_id='user_456')
        log_mgr.start()
        logger = log_mgr.get_logger('my_module')
        logger.info("Processing started")
        # ... do work ...
        log_mgr.shutdown()  # Flushes remaining logs
    """
    
    def __init__(self, job_id: str, user_id: Optional[str] = None):
        self.job_id = job_id
        self.user_id = user_id or 'unknown'
        self.log_queue: 'queue.Queue' = queue.Queue(maxsize=config.log_queue_maxsize)
        self.consumer: Optional[LogConsumer] = None
    
    def start(self):
        """Start the background log consumer thread."""
        self.consumer = LogConsumer(self.log_queue, self.job_id, self.user_id)
        self.consumer.start()
        
        # Configure the root logger to use our custom handler.
        root_logger = logging.getLogger()
        root_logger.setLevel(config.log_level)
        
        # Remove any existing handlers to avoid duplicates.
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our custom Supabase handler.
        handler = SupabaseStorageHandler(self.log_queue)
        root_logger.addHandler(handler)
        
        # Also add a console handler for visibility during development.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        logger.info(f"BufferedLogger started for job {self.job_id}, user {self.user_id}")
    
    def shutdown(self):
        """
        Gracefully shut down the log consumer.
        
        Sends a sentinel (None) to signal the consumer to flush and exit.
        """
        if self.consumer and self.consumer.is_alive():
            logger.info("Sending shutdown signal to LogConsumer")
            self.log_queue.put(None)  # Sentinel value
            self.consumer.join(timeout=5)
            
            if self.consumer.is_alive():
                logger.warning("LogConsumer did not shut down within 5 seconds")
            else:
                logger.info("LogConsumer shut down cleanly")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(name)


# Shutdown hook: ensure logs are flushed if the process terminates unexpectedly.
_buffered_logger_instance: Optional[BufferedLogger] = None

def _shutdown_hook():
    """Registered with atexit to gracefully flush logs on process exit."""
    if _buffered_logger_instance:
        _buffered_logger_instance.shutdown()

atexit.register(_shutdown_hook)


def setup_buffered_logging(job_id: str, user_id: Optional[str] = None) -> BufferedLogger:
    """
    Factory function to set up buffered logging for a job.
    
    Args:
        job_id: Unique identifier for the job.
        user_id: Optional user identifier for organizing logs.
    
    Returns:
        BufferedLogger instance (already started).
    """
    global _buffered_logger_instance
    _buffered_logger_instance = BufferedLogger(job_id, user_id)
    _buffered_logger_instance.start()
    return _buffered_logger_instance

