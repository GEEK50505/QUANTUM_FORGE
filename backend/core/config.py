"""
Configuration management for QUANTUM_FORGE logging and automation.
"""
import os
from pathlib import Path


class Config:
    """Configuration class for QUANTUM_FORGE automation pipeline."""
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs/")
    LOG_FORMAT_CONSOLE = "[%(asctime)s] %(name)s [%(levelname)s]: %(message)s"
    LOG_FORMAT_FILE = "[%(asctime)s] %(name)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s"
    
    # xTB execution configuration
    XTB_TIMEOUT = int(os.getenv("XTB_TIMEOUT", "300"))
    XTB_MAX_RETRIES = int(os.getenv("XTB_MAX_RETRIES", "2"))
    
    # Directory configuration
    WORKDIR = os.getenv("WORKDIR", "runs/")
    DATA_DIR = os.getenv("DATA_DIR", "data/molecules/")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "results/")


def get_config() -> Config:
    """
    Get the configuration instance.
    
    Returns:
        Config instance with current settings
    """
    return Config()