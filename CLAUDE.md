# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


All the changes must be implemented on a ad-hoc branch. 
If the task was already initiate, the existing branch should be used.
Create an issue on github in order to define a new branch. 
The branch must be push on github.
A request to the user must be raised before the branch is merged on main.


## Project Overview

This is `python-codicefiscale`, a Python library for encoding/decoding Italian fiscal codes (Codice Fiscale). The library provides both a Python API and CLI interface for working with Italian tax codes.

## Development Commands

### Testing
```bash
# Run all tests with coverage (minimum 90% required)
pytest tests --cov=codicefiscale --cov-report=term-missing --cov-fail-under=90

# Run tests across multiple Python versions
tox

# Run single test file
pytest tests/test_encode.py
```

### Code Quality
```bash
# Run all linting and formatting checks
pre-commit run -a

# Type checking
mypy --install-types --non-interactive --strict

# Manual formatting (though pre-commit handles this)
black .
ruff check .
```

### Package Building
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt -r requirements-test.txt

# Setup pre-commit hooks
pre-commit install --install-hooks
```

### CLI Usage
```bash
# Encode fiscal code
python -m codicefiscale encode --firstname Fabio --lastname Caccamo --gender M --birthdate 03/04/1985 --birthplace Torino

# Decode fiscal code
python -m codicefiscale decode CCCFBA85D03L219P
```

### FastAPI Server Usage
```bash
# Install API dependencies
uv add "python-codicefiscale[api]"

# Start the API server
python -m codicefiscale.__main_api__

# Or with custom host/port
uvicorn codicefiscale.app:app --host 0.0.0.0 --port 8000 --reload
```

### Package Management
This project uses `uv` for dependency management:
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Run commands in virtual environment
uv run python -m pytest
uv run python -m codicefiscale.__main_api__
```

## Architecture

### Core Module Structure
- `codicefiscale/codicefiscale.py`: Main encoding/decoding logic with algorithms for fiscal code calculation
- `codicefiscale/partitaiva.py`: Italian VAT number (Partita IVA) validation and encoding
- `codicefiscale/data.py`: Data management for municipalities and countries with auto-update capability 
- `codicefiscale/cli.py`: Command-line interface implementation
- `codicefiscale/__main__.py`: CLI entry point
- `codicefiscale/metadata.py`: Package metadata and version information

### FastAPI Web Application (Optional)
- `codicefiscale/app.py`: REST API server with validation endpoints
- `codicefiscale/auth.py`: Clerk authentication integration for API security
- `codicefiscale/__main_api__.py`: API server entry point

### Key Features
- **Fiscal Code Support**: Complete encoding/decoding with omocodia handling
- **VAT Number Support**: Italian Partita IVA validation with proper check digit calculation
- **REST API**: Optional FastAPI server with authentication support
- **Auto-updated data**: Municipality and country data automatically updated weekly from ANPR
- **Flexible date parsing**: Multiple birthdate formats supported via python-dateutil
- **Transliteration**: Name/surname handling for non-ASCII characters
- **Comprehensive validation**: Full fiscal code and VAT number structure validation

### Data Files
Located in `codicefiscale/data/`:
- `municipalities.json`: Italian municipality codes and names
- `countries.json`: Foreign country codes  
- `*-patch.json`: Manual corrections to auto-updated data
- `deleted-countries.json`: Historical country codes no longer valid

### Dependencies

#### Core Dependencies
- `python-dateutil`: Date parsing flexibility
- `python-fsutil`: File system utilities
- `python-slugify`: Text normalization

#### Optional API Dependencies
Install with `pip install 'python-codicefiscale[api]'`:
- `fastapi`: Web framework for REST API
- `uvicorn`: ASGI server for FastAPI
- `pyjwt[crypto]`: JWT token handling for authentication
- `cryptography`: Cryptographic operations
- `python-dotenv`: Environment variable management

## Testing Strategy

Tests are organized by functionality:
- `test_encode.py`: Fiscal code generation tests
- `test_decode.py`: Fiscal code parsing tests  
- `test_cli.py`: Command-line interface tests
- `test_partitaiva.py`: VAT number validation tests
- `test_api.py`: FastAPI endpoint tests (skipped if dependencies not available)
- `test_auth.py`: Authentication system tests
- `issues/`: Regression tests for specific GitHub issues

The project maintains 90% test coverage requirement and uses pytest with coverage reporting.

## Authentication System

The FastAPI application supports optional Clerk authentication:

### Environment Variables
```bash
# Required for authentication (set one or both)
CLERK_PUBLISHABLE_KEY=pk_test_xxx...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx...

# Optional
CLERK_SECRET_KEY=sk_test_xxx...
```

### Authentication Behavior
- **No credentials**: All endpoints are public, no authentication required
- **With credentials**: Protected endpoints require valid JWT Bearer token
- **Health endpoint**: Always public regardless of auth settings

### API Endpoints
When authentication is enabled:
```bash
# Public endpoints
GET /          # API info (shows current user if authenticated)  
GET /health    # Health check

# Protected endpoints (require Authorization: Bearer <token>)
POST /fiscal-code/validate    # Validate fiscal code
POST /fiscal-code/encode      # Generate fiscal code  
POST /fiscal-code/decode      # Parse fiscal code
POST /vat/validate           # Validate VAT number
POST /vat/encode             # Generate VAT number
POST /vat/decode             # Parse VAT number
```

### Testing Authentication
Use the included test script:
```bash
python test_clerk_auth.py
```

This script will:
- Check environment variable configuration
- Verify Clerk authentication setup
- Test API endpoints with/without authentication
- Provide debugging information

### Authentication Setup
For complete authentication setup instructions, see [AUTHENTICATION.md](AUTHENTICATION.md).

Quick setup:
1. Create Clerk account and application
2. Set environment variables:
   ```bash
   CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
   CLERK_SECRET_KEY=sk_test_your_secret_here
   ```
3. Obtain JWT token from Clerk authentication flow
4. Use token in API requests: `Authorization: Bearer <token>`

### Known Issues with Authentication
- JWT signature verification is disabled for demo purposes (see `codicefiscale/auth.py:57`)
- For production use, implement proper JWKS fetching and signature verification
- Empty string environment variables are properly filtered out (fixed in recent updates)