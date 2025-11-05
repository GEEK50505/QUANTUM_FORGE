#!/usr/bin/env python3
"""
Run the QUANTUM_FORGE FastAPI server
"""

import argparse
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main function to run the API server"""
    parser = argparse.ArgumentParser(description="Run QUANTUM_FORGE API server")
    parser.add_argument(
        "--host", 
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("API_RELOAD", "False").lower() == "true",
        help="Enable auto-reload on code changes"
    )
    
    args = parser.parse_args()
    
    print(f"API server starting on http://{args.host}:{args.port}")
    print("Press CTRL+C to stop the server")
    
    # Run the server
    uvicorn.run(
        "backend.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()