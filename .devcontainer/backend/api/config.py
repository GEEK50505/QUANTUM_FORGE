import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for QUANTUM_FORGE API"""
    
    # API Configuration
    API_TITLE = "QUANTUM_FORGE"
    API_VERSION = "0.1.0"
    
    # Directory Configuration
    JOBS_DIR = os.getenv("JOBS_DIR", "jobs/")
    WORKDIR = os.getenv("WORKDIR", "runs/")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # Database Configuration (optional, for future use)
    DATABASE_URL = os.getenv("DATABASE_URL", None)
    
    # xTB Configuration
    XTB_TIMEOUT = int(os.getenv("XTB_TIMEOUT", "300"))
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        # Ensure directories exist
        os.makedirs(cls.JOBS_DIR, exist_ok=True)
        os.makedirs(cls.WORKDIR, exist_ok=True)
        
        # Validate CORS origins
        cls.CORS_ORIGINS = [origin.strip() for origin in cls.CORS_ORIGINS]
        
        return cls