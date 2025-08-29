"""
Google Cloud Function optimized version of the FastAPI application.

This module creates a version of the FastAPI app specifically optimized
for Google Cloud Functions deployment.
"""

from __future__ import annotations

import os
from typing import Any, Optional

# Check if we're running in Google Cloud Function environment
IS_CLOUD_FUNCTION = os.getenv('GOOGLE_CLOUD_FUNCTION', '').lower() == '1'

try:
    from dotenv import load_dotenv
    from fastapi import Depends, FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel, Field
    
    # Only load .env in local development, not in Cloud Functions
    if not IS_CLOUD_FUNCTION:
        load_dotenv()
        
except ImportError as e:
    raise ImportError(
        "FastAPI dependencies not installed. "
        "Install with: pip install -r requirements-cloudfunction.txt"
    ) from e

from . import codicefiscale, partitaiva

# Import authentication only if enabled (check both env var names)
def _get_non_empty_env(key: str) -> str | None:
    value = os.getenv(key)
    return value if value and value.strip() else None

AUTH_ENABLED = (
    _get_non_empty_env("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") is not None
    or _get_non_empty_env("CLERK_PUBLISHABLE_KEY") is not None
)

if AUTH_ENABLED:
    try:
        from .auth import clerk_auth, get_user_metadata, optional_clerk_auth
    except (ImportError, ValueError):
        AUTH_ENABLED = False

# Optimize description for Cloud Functions
description = "REST API for validating Italian fiscal codes (Codice Fiscale) and VAT numbers (Partita IVA)"
if AUTH_ENABLED:
    description += "\n\n**Authentication**: This API uses Clerk authentication. Include your Bearer token in the Authorization header."

if IS_CLOUD_FUNCTION:
    description += "\n\n**Deployed on**: Google Cloud Functions"

# Create FastAPI app with Cloud Function optimizations
app = FastAPI(
    title="Italian Fiscal Code and VAT Number Validation API",
    description=description,
    version="1.0.0",
    docs_url="/docs" if not IS_CLOUD_FUNCTION else "/docs",  # Keep docs available
    redoc_url="/redoc" if not IS_CLOUD_FUNCTION else "/redoc",
)

# Template setup - only in non-Cloud Function environments or if templates exist
from pathlib import Path
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# For Cloud Functions, we might not have static files
if not IS_CLOUD_FUNCTION and static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates if available
templates = None
if templates_dir.exists():
    templates = Jinja2Templates(directory=templates_dir)


# Pydantic models
class FiscalCodeRequest(BaseModel):
    code: str = Field(..., description="The fiscal code to validate")


class VATRequest(BaseModel):
    partita_iva: str = Field(..., description="The VAT number to validate")


class FiscalCodeEncodeRequest(BaseModel):
    lastname: str = Field(..., description="Last name")
    firstname: str = Field(..., description="First name")
    gender: str = Field(..., description="Gender (M/F)")
    birthdate: str = Field(..., description="Birth date (various formats supported)")
    birthplace: str = Field(..., description="Birth place name")


class VATEncodeRequest(BaseModel):
    base_number: str = Field(..., description="First 10 digits of VAT number")


class ValidationResponse(BaseModel):
    valid: bool
    code: str
    details: dict[str, Any] | None = None


# Set up dependencies based on auth status
def no_auth() -> dict[str, Any]:
    """Dummy auth dependency when authentication is disabled."""
    return {}

if AUTH_ENABLED:
    auth_dependency = Depends(clerk_auth)
    optional_auth_dependency = Depends(optional_clerk_auth)
else:
    auth_dependency = Depends(no_auth)
    optional_auth_dependency = Depends(no_auth)


# Root endpoint - prioritize API info for Cloud Functions
@app.get("/", response_class=HTMLResponse if templates and not IS_CLOUD_FUNCTION else JSONResponse)
async def root(request: Request = None, auth_data: dict[str, Any] = optional_auth_dependency):
    """Root endpoint - web interface in development, API info in Cloud Functions."""
    # In Cloud Functions, prioritize JSON API response
    if IS_CLOUD_FUNCTION or templates is None:
        return await api_info(auth_data)
    
    # In development, show web interface
    user_info = None
    if AUTH_ENABLED and auth_data and "sub" in auth_data:
        user_info = get_user_metadata(auth_data)
    
    return templates.TemplateResponse(request, "index.html", {
        "auth_enabled": AUTH_ENABLED,
        "user": user_info
    })


@app.get("/api", response_class=JSONResponse)
async def api_info(auth_data: dict[str, Any] = optional_auth_dependency):
    """API information endpoint."""
    response = {
        "name": "Italian Fiscal Code and VAT Number Validation API",
        "version": "1.0.0",
        "environment": "Google Cloud Functions" if IS_CLOUD_FUNCTION else "Development",
        "authentication": {
            "enabled": AUTH_ENABLED,
            "type": "Clerk JWT Bearer Token" if AUTH_ENABLED else "None",
        },
        "endpoints": {
            "fiscal_code": {
                "validate": "POST /fiscal-code/validate",
                "encode": "POST /fiscal-code/encode",
                "decode": "POST /fiscal-code/decode",
            },
            "vat": {
                "validate": "POST /vat/validate",
                "encode": "POST /vat/encode",
                "decode": "POST /vat/decode",
            },
        },
    }
    
    # Add user info if authenticated
    if AUTH_ENABLED and auth_data and "sub" in auth_data:
        response["user"] = get_user_metadata(auth_data)
    
    return response


@app.post("/fiscal-code/validate", response_model=ValidationResponse)
async def validate_fiscal_code(
    request: FiscalCodeRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Validate an Italian fiscal code."""
    try:
        is_valid = codicefiscale.is_valid(request.code)
        return ValidationResponse(
            valid=is_valid,
            code=request.code,
            details={"is_omocode": codicefiscale.is_omocode(request.code)} if is_valid else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/fiscal-code/encode")
async def encode_fiscal_code(
    request: FiscalCodeEncodeRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Generate a fiscal code from personal data."""
    try:
        encoded_code = codicefiscale.encode(
            lastname=request.lastname,
            firstname=request.firstname,
            gender=request.gender,
            birthdate=request.birthdate,
            birthplace=request.birthplace,
        )
        return {"code": encoded_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/fiscal-code/decode")
async def decode_fiscal_code(
    request: FiscalCodeRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Decode a fiscal code to extract personal data."""
    try:
        decoded_data = codicefiscale.decode(request.code)
        return decoded_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/vat/validate", response_model=ValidationResponse)
async def validate_vat(
    request: VATRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Validate an Italian VAT number (Partita IVA)."""
    try:
        is_valid = partitaiva.is_valid(request.partita_iva)
        return ValidationResponse(
            valid=is_valid,
            code=request.partita_iva,
            details=partitaiva.decode(request.partita_iva) if is_valid else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/vat/encode")
async def encode_vat(
    request: VATEncodeRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Generate a complete VAT number from base 10 digits."""
    try:
        encoded_vat = partitaiva.encode(request.base_number)
        return {"partita_iva": encoded_vat}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/vat/decode")
async def decode_vat(
    request: VATRequest,
    auth_data: dict[str, Any] = auth_dependency
):
    """Decode a VAT number to extract its components."""
    try:
        decoded_data = partitaiva.decode(request.partita_iva)
        return decoded_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# Health check endpoint - always available
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_info = {
        "status": "healthy",
        "environment": "Google Cloud Functions" if IS_CLOUD_FUNCTION else "Development",
        "authentication_enabled": AUTH_ENABLED
    }
    
    if IS_CLOUD_FUNCTION:
        # Add Cloud Function specific health info
        health_info["function_name"] = os.getenv("K_SERVICE", "fiscal-code-api")
        health_info["function_revision"] = os.getenv("K_REVISION", "unknown")
    
    return health_info


# Startup event for logging
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    if IS_CLOUD_FUNCTION:
        print(f"🚀 Starting Italian Fiscal Code API on Google Cloud Functions")
        print(f"📊 Authentication: {'Enabled' if AUTH_ENABLED else 'Disabled'}")
    else:
        print(f"🚀 Starting Italian Fiscal Code API in development mode")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)