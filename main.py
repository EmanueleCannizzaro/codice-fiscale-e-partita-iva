#!/usr/bin/env python3
"""
Google Cloud Function entry point for Italian Fiscal Code & VAT Validation API.

This module adapts the FastAPI application to work as a Google Cloud Function
using the Functions Framework.
"""

import os
from typing import Any

# Set Cloud Function environment flag
os.environ['GOOGLE_CLOUD_FUNCTION'] = '1'

try:
    import functions_framework
    from flask import Request
except ImportError as e:
    raise ImportError(
        "Cloud Function dependencies not installed. "
        "Install with: pip install functions-framework"
    ) from e

# Import the Cloud Function optimized FastAPI app
from codicefiscale.cloud_function_app import app

# Convert FastAPI app to ASGI callable for Functions Framework
from mangum import Mangum

# Create the handler for Google Cloud Functions
handler = Mangum(app, lifespan="off")


@functions_framework.http
def fiscal_code_api(request: Request) -> Any:
    """
    Google Cloud Function HTTP entry point.
    
    This function receives HTTP requests and forwards them to the FastAPI
    application via the Mangum ASGI adapter.
    
    Args:
        request: Flask Request object from Google Cloud Functions
        
    Returns:
        HTTP response from the FastAPI application
    """
    # Convert Flask request to ASGI format and process
    scope = {
        "type": "http",
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string,
        "headers": [
            [key.lower().encode(), value.encode()]
            for key, value in request.headers.items()
        ],
    }
    
    # Handle the request through Mangum (FastAPI -> ASGI -> Cloud Function)
    return handler(scope, None, None)


# For local testing with Functions Framework
if __name__ == "__main__":
    import subprocess
    import sys
    
    print("Starting local Functions Framework server...")
    print("API will be available at: http://localhost:8080")
    print("Health check: http://localhost:8080/health")
    print("API docs: http://localhost:8080/docs")
    print("Press Ctrl+C to stop")
    
    # Start the Functions Framework development server
    try:
        subprocess.run([
            sys.executable, "-m", "functions_framework",
            "--target", "fiscal_code_api",
            "--port", "8080",
            "--debug"
        ])
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except FileNotFoundError:
        print("ERROR: functions-framework not installed.")
        print("Install with: pip install functions-framework")
        sys.exit(1)