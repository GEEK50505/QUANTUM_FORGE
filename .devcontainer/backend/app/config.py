"""
Application Configuration

Reads settings from environment variables (.env file).
Supports multiple deployment scenarios:
- Local development with SQLite or local PostgreSQL
- Docker development with Supabase PostgreSQL
- Production with Supabase PostgreSQL
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Settings:
    """
    Application settings from environment variables.
    
    Supports .env files and environment variable overrides.
    Examples:
        - DATABASE_URL=postgresql://...
        - Or: DB_USER=postgres DB_PASSWORD=xxx DB_HOST=localhost
    """
    
    # Supabase / Database
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # Direct database connection (alternative to Supabase)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DB_USER: Optional[str] = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    DB_PORT: Optional[int] = int(os.getenv("DB_PORT", "5432")) if os.getenv("DB_PORT") else None
    DB_NAME: Optional[str] = os.getenv("DB_NAME", "postgres")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    APP_NAME: str = "Quantum Forge"
    APP_VERSION: str = "1.0.0"
    
    # XTB
    XTB_PATH: Optional[str] = os.getenv("XTB_PATH")
    XTB_VERSION: Optional[str] = os.getenv("XTB_VERSION", "6.7.1")
    
    # Execution
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "300"))


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    
    Caches result to avoid repeated environment variable lookups.
    
    Returns:
        Settings instance
    """
    return Settings()


def validate_database_config() -> tuple[bool, str]:
    """
    Validate that database configuration is present and valid.
    
    Returns:
        Tuple of (is_valid, message)
    """
    settings = get_settings()
    
    # Check for database URL
    if settings.DATABASE_URL:
        if "postgresql://" not in settings.DATABASE_URL:
            return False, "DATABASE_URL must use postgresql:// scheme"
        return True, "DATABASE_URL configured"
    
    # Check for component-based config
    if not settings.DB_HOST:
        return False, "Either DATABASE_URL or DB_HOST must be set"
    
    if not settings.DB_PASSWORD:
        return False, "DB_PASSWORD is required"
    
    return True, f"Database configured for {settings.DB_HOST}"
