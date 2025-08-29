#!/usr/bin/env python3
"""
Entry point for running the FastAPI validation server.
"""

if __name__ == "__main__":
    try:
        import uvicorn

        from codicefiscale.app import app

        print("Starting Italian Fiscal Code and VAT Number Validation API server...")
        print("API Documentation available at: http://localhost:8000/docs")
        print("Health check available at: http://localhost:8000/health")

        uvicorn.run("codicefiscale.app:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("ERROR: FastAPI dependencies not installed.")
        print("Install with: pip install 'python-codicefiscale[api]'")
        exit(1)
