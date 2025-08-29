from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError as e:
    raise ImportError(
        "FastAPI dependencies not installed. "
        "Install with: pip install 'python-codicefiscale[api]'"
    ) from e

from . import codicefiscale
from . import partitaiva


app = FastAPI(
    title="Italian Fiscal Code and VAT Number Validation API",
    description="REST API for validating Italian fiscal codes (Codice Fiscale) and VAT numbers (Partita IVA)",
    version="1.0.0",
)


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


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Italian Fiscal Code and VAT Number Validation API",
        "version": "1.0.0",
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


@app.post("/fiscal-code/validate", response_model=ValidationResponse)
async def validate_fiscal_code(request: FiscalCodeRequest):
    """Validate an Italian fiscal code."""
    try:
        is_valid = codicefiscale.is_valid(request.code)
        return ValidationResponse(
            valid=is_valid,
            code=request.code,
            details={"is_omocode": codicefiscale.is_omocode(request.code)} if is_valid else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fiscal-code/encode")
async def encode_fiscal_code(request: FiscalCodeEncodeRequest):
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
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fiscal-code/decode")
async def decode_fiscal_code(request: FiscalCodeRequest):
    """Decode a fiscal code to extract personal data."""
    try:
        decoded_data = codicefiscale.decode(request.code)
        return decoded_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/vat/validate", response_model=ValidationResponse)
async def validate_vat(request: VATRequest):
    """Validate an Italian VAT number (Partita IVA)."""
    try:
        is_valid = partitaiva.is_valid(request.partita_iva)
        return ValidationResponse(
            valid=is_valid,
            code=request.partita_iva,
            details=partitaiva.decode(request.partita_iva) if is_valid else None,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/vat/encode")
async def encode_vat(request: VATEncodeRequest):
    """Generate a complete VAT number from base 10 digits."""
    try:
        encoded_vat = partitaiva.encode(request.base_number)
        return {"partita_iva": encoded_vat}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/vat/decode")
async def decode_vat(request: VATRequest):
    """Decode a VAT number to extract its components."""
    try:
        decoded_data = partitaiva.decode(request.partita_iva)
        return decoded_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)