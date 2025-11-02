"""
Centralized logging configuration for QUANTUM_FORGE platform.
"""
import logging
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import time


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Create and configure a logger with both console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "[%(asctime)s] %(name)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = logs_dir / f"{name}.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "[%(asctime)s] %(name)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


@contextmanager
def log_execution_time(logger: logging.Logger, operation_name: str):
    """
    Context manager to log execution time of operations.
    
    Args:
        logger: Logger instance to use
        operation_name: Name of the operation being timed
    """
    start_time = time.time()
    logger.debug(f"Starting {operation_name}")
    try:
        yield
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Completed {operation_name} in {execution_time:.3f} seconds")