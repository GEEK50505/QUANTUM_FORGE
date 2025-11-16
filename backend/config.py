"""
Environment and xTB configuration for Quantum_Forge platform.
"""
import os
import logging
from pathlib import Path


class XTBConfig:
    """xTB execution configuration"""
    
    def __init__(self, **overrides):
        # Find xTB executable in system PATH
        # Default configuration; environment variables are respected
        self.XTB_EXECUTABLE = self._find_xtb_executable()
        self.XTB_TIMEOUT = int(os.getenv("XTB_TIMEOUT", "300"))  # 300 seconds default
        self.WORKDIR = os.getenv("WORKDIR", "./runs/")
        self.JOBS_DIR = os.getenv("JOBS_DIR", "./jobs/")
        self.LOG_DIR = os.getenv("LOG_DIR", "./logs/")

        # Override configuration for testing or runtime injection
        for key, value in overrides.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Create directories if they don't exist
        Path(self.WORKDIR).mkdir(parents=True, exist_ok=True)
        Path(self.JOBS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.LOG_DIR).mkdir(parents=True, exist_ok=True)
        
        # Validate xTB exists and is executable
        self._validate_xtb()
    
    def _find_xtb_executable(self) -> str | None:
        """Find xTB executable in system PATH"""
        import shutil
        xtb_path = shutil.which("xtb")
        if xtb_path is None:
            # In dev mode without xTB, return None - will be handled gracefully
            return None
        return xtb_path
    
    def _validate_xtb(self):
        """Validate that xTB exists and is executable"""
        if self.XTB_EXECUTABLE is None:
            # Development mode - xTB not available, but that's okay for API-only work
            return
        if not os.path.exists(self.XTB_EXECUTABLE):
            raise RuntimeError(f"xTB executable not found at {self.XTB_EXECUTABLE}")
        if not os.access(self.XTB_EXECUTABLE, os.X_OK):
            raise RuntimeError(f"xTB executable is not executable: {self.XTB_EXECUTABLE}")


class AppConfig:
    """Application configuration"""
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"


class LogConfig:
    """Logging configuration"""
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # Directory to write log files to. Tests and code expect this attribute to exist
    LOG_DIR = os.getenv("LOG_DIR", "./logs/")


def validate_environment() -> bool:
    """
    Validate environment setup
    
    Returns:
        bool: True if environment is valid
    """
    try:
        # Validate xTB configuration
        xtb_config = XTBConfig()
        
        # Create required directories
        Path(xtb_config.WORKDIR).mkdir(parents=True, exist_ok=True)
        Path(xtb_config.JOBS_DIR).mkdir(parents=True, exist_ok=True)
        Path(xtb_config.LOG_DIR).mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        logging.error(f"Environment validation failed: {e}")
        return False


def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger for any module
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LogConfig.LOG_LEVEL, logging.DEBUG))
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LogConfig.LOG_LEVEL, logging.DEBUG))
        console_formatter = logging.Formatter(LogConfig.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path(LogConfig.LOG_DIR) / "quantum_forge.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, LogConfig.LOG_LEVEL, logging.DEBUG))
        file_formatter = logging.Formatter(LogConfig.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger