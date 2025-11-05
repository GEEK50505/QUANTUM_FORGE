from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
from typing import Optional
import os
from dotenv import load_dotenv

from .routes import router
from .config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description="QUANTUM_FORGE xTB job management API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.2f}s")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add processing time header"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": "An unexpected error occurred"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation exception handler"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNVALIDATABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "error_message": "Request validation failed",
            "details": exc.errors()
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "version": Config.API_VERSION}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Include routes
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("QUANTUM_FORGE API starting up...")
    
    # Create jobs directory if it doesn't exist
    os.makedirs(Config.JOBS_DIR, exist_ok=True)
    logger.info(f"Jobs directory ready: {Config.JOBS_DIR}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("QUANTUM_FORGE API shutting down...")