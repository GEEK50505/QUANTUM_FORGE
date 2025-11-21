"""
Supabase Database Connection and Session Management

Provides:
- SQLAlchemy engine and session factory configured for Supabase PostgreSQL
- Connection pooling for 50+ concurrent connections
- Health check utilities
- Automatic table initialization
- Context managers for database operations
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine import Engine

from backend.app.config import get_settings

logger = logging.getLogger(__name__)

# Global references
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def get_database_url() -> str:
    """
    Construct database URL from environment variables.
    
    For Supabase:
    - USER: postgres or service_role
    - PASSWORD: Supabase password
    - HOST: Project reference.supabase.co
    - PORT: 5432
    - DB: postgres (or custom)
    
    Returns:
        PostgreSQL connection string in SQLAlchemy format
    """
    settings = get_settings()
    
    # Use DATABASE_URL if provided (from .env)
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # Otherwise construct from components
    db_user = settings.DB_USER or "postgres"
    db_password = settings.DB_PASSWORD
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT or 5432
    db_name = settings.DB_NAME or "postgres"
    
    if not db_password or not db_host:
        raise ValueError(
            "Database credentials missing. Set DATABASE_URL or "
            "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME"
        )
    
    url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return url


def create_db_engine(
    database_url: Optional[str] = None,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 30,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
) -> Engine:
    """
    Create SQLAlchemy engine with connection pooling.
    
    Configured for Supabase with:
    - QueuePool: Manages 20 connections + 30 overflow (handles 50+ concurrent)
    - Pool recycling: Recycle connections every 3600s (Supabase timeout)
    - SQL echo: Optional debug logging of all SQL statements
    
    Args:
        database_url: PostgreSQL connection string (uses env if not provided)
        echo: Log all SQL statements (debug)
        pool_size: Number of connections to maintain
        max_overflow: Additional connections above pool_size
        pool_timeout: Seconds to wait for available connection
        pool_recycle: Seconds before connection recycled (Supabase default ~5min)
    
    Returns:
        Configured SQLAlchemy engine
    
    Raises:
        ValueError: If database URL cannot be constructed
    """
    if not database_url:
        database_url = get_database_url()
    
    logger.info(f"Creating database engine for {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    
    # Create engine with connection pooling
    engine = create_engine(
        database_url,
        echo=echo,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Test connections before use
        connect_args={
            "connect_timeout": 30,
            "application_name": "quantum_forge_api",
        }
    )
    
    # Register event listeners for debugging
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log successful connections"""
        logger.debug("Database connection established")
    
    return engine


def init_db(engine: Engine) -> None:
    """
    Initialize database: create all tables and indexes.
    
    Uses SQLAlchemy metadata to create tables defined in models.py.
    Safe to call repeatedly (only creates missing tables).
    
    For new deployments:
    1. Use backend/scripts/schema.sql for full setup with RLS
    2. Or call this function to create tables only
    
    Args:
        engine: SQLAlchemy engine
    
    Raises:
        Exception: If table creation fails
    """
    try:
        from backend.app.db.models import Base
        
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_session_factory(engine: Engine) -> sessionmaker:
    """
    Create session factory for the engine.
    
    Args:
        engine: SQLAlchemy engine
    
    Returns:
        Session factory configured for thread-safe usage
    """
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )


def setup_database() -> tuple[Engine, sessionmaker]:
    """
    One-time setup: create engine, session factory, and initialize tables.
    
    Call this once at application startup.
    
    Returns:
        Tuple of (engine, SessionLocal factory)
    """
    global engine, SessionLocal
    
    try:
        # Create engine
        engine = create_db_engine()
        
        # Create session factory
        SessionLocal = get_session_factory(engine)
        
        # Initialize tables
        init_db(engine)
        
        logger.info("Database setup completed successfully")
        return engine, SessionLocal
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI routes.
    
    Usage in route:
        @app.get("/molecules")
        def list_molecules(db: Session = Depends(get_db)):
            return db.query(Molecule).all()
    
    Yields:
        SQLAlchemy session
        
    Ensures:
        - Connection returned to pool after use
        - Transaction rolled back on error
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call setup_database() at startup.")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database access (non-FastAPI usage).
    
    Usage:
        with get_db_context() as db:
            molecules = db.query(Molecule).all()
    
    Yields:
        SQLAlchemy session
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call setup_database() at startup.")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_db_health(engine: Engine) -> dict:
    """
    Health check: verify database connection and key operations.
    
    Returns:
        Dict with status and details:
        {
            "status": "healthy" | "unhealthy",
            "database": "postgres",
            "pool_size": 20,
            "tables_exist": True,
            "message": "Details here"
        }
    """
    try:
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT 1"))
            result.close()
            
            # Check tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = {
                "molecules", "calculations", "atomic_properties",
                "batch_jobs", "batch_items", "event_logs"
            }
            
            missing_tables = required_tables - set(tables)
            
            if missing_tables:
                return {
                    "status": "unhealthy",
                    "database": "postgres",
                    "message": f"Missing tables: {missing_tables}",
                    "tables_exist": False,
                }
            
            return {
                "status": "healthy",
                "database": "postgres",
                "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "unknown",
                "tables_exist": True,
                "message": f"Connected successfully. {len(tables)} tables exist."
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "postgres",
            "message": str(e),
            "tables_exist": False,
        }


def close_db() -> None:
    """
    Close database connection pool (called on app shutdown).
    """
    global engine
    if engine:
        logger.info("Closing database connections...")
        engine.dispose()
        engine = None
