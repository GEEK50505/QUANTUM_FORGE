"""
Compatibility re-exports for backend.api

Expose the FastAPI `app`, router and JobManager under the
`backend.app.api` namespace so consumers can import stable symbols
during reorganization.
"""

from backend.api.main import app  # FastAPI application
from backend.api.routes import router
from backend.api.job_manager import JobManager

__all__ = ["app", "router", "JobManager"]
