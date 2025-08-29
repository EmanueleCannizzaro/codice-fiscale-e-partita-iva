from __future__ import annotations

import os
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    from fastapi import Depends, FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel, Field
    
    # Load environment variables from .env file
    load_dotenv()
except ImportError as e:
    raise ImportError(
        "FastAPI dependencies not installed. "
        "Install with: pip install 'python-codicefiscale[api]'"
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

description = "REST API for validating Italian fiscal codes (Codice Fiscale) and VAT numbers (Partita IVA)"
if AUTH_ENABLED:
    description += "\n\n**Authentication**: This API uses Clerk authentication. Include your Bearer token in the Authorization header."

app = FastAPI(
    title="Italian Fiscal Code and VAT Number Validation API",
    description=description,
    version="1.0.0",
)

# Template setup
from pathlib import Path
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# Only mount static files if the directory exists
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Only setup templates if the directory exists
templates = None
if templates_dir.exists():
    templates = Jinja2Templates(directory=templates_dir)


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


@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request, auth_data: dict[str, Any] = optional_auth_dependency):
    """Web interface for fiscal code and VAT validation."""
    if templates is None:
        # Fallback to JSON response if templates not available
        return await api_info(auth_data)
    
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
