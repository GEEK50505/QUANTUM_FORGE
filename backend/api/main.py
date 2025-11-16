"""
FastAPI app with xTB config, CORS, logging middleware.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from backend.config import XTBConfig, AppConfig, validate_environment, get_logger
from backend.api.routes import router

# Configure logging
logger = get_logger(__name__)

def log_requests_middleware(app: FastAPI):
    """Add request logging middleware"""
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware to log all requests and responses"""
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"{response.status_code} OK ({process_time*1000:.0f}ms)")
            
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    return app

# Validate environment on startup
logger.info("Validating environment...")
try:
    if not validate_environment():
        logger.warning("Environment validation failed - running in limited mode (xTB may not be available)")
except Exception as e:
    logger.warning(f"Environment validation warning: {e} - running in limited mode (xTB may not be available)")

# Create FastAPI app
app = FastAPI(
    title="Quantum_Forge",
    version="0.1.0",
    description="Quantum molecular simulation platform with xTB integration"
)

# Add logging middleware
app = log_requests_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[AppConfig.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation exception handler"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "version": "0.1.0"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # instantiate to validate xTB availability; no local variable required
        XTBConfig()
        return {"status": "healthy", "xTB": "available"}
    except Exception as e:
        return {"status": "unhealthy", "xTB": str(e)}

# Include routes
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("API server starting")
    
    # Validate xTB configuration
    try:
        xtb_config = XTBConfig()
        logger.info(f"xTB executable: {xtb_config.XTB_EXECUTABLE}")
        logger.info(f"Working directory: {xtb_config.WORKDIR}")
        logger.info(f"Jobs directory: {xtb_config.JOBS_DIR}")
        logger.info(f"Log directory: {xtb_config.LOG_DIR}")
    except Exception as e:
        logger.error(f"xTB configuration error: {e}")
        raise
    
    logger.info("API server ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("API server shutting down")