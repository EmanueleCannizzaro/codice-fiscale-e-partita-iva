# Frontend - Clerk JWT Token Generator

This frontend application provides JWT token generation and API testing tools for the Python FastAPI backend.

## Overview

This Node.js application generates valid Clerk JWT tokens for testing the main Python FastAPI application. It's designed to solve authentication issues during development and testing.

## Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Generate JWT token
npm run token

# Test the Python API
npm run test-api
```

## Project Structure

```
frontend/
├── README.md                    # This file
├── package.json                 # Node.js dependencies and scripts
├── generate-token.js           # Main JWT token generator
├── test-api.js                 # API testing suite
├── test-example.js             # Usage examples
├── CLERK_TOKEN_GENERATOR.md    # Detailed documentation
└── .token                      # Generated token (auto-created)
```

## Available Scripts

- **`npm run token`** - Generate a new JWT token
- **`npm run test-api`** - Run comprehensive API tests  
- **`npm start`** - Alias for token generation
- **`node test-api.js --interactive`** - Interactive testing mode
- **`node test-example.js`** - Run usage examples

## Features

🔐 **Token Generation**
- Creates valid JWT tokens from your Clerk configuration
- Proper 3-segment format (header.payload.signature)
- Includes all required Clerk claims
- 24-hour token expiration

🧪 **API Testing**
- Tests all Python FastAPI endpoints
- Validates authentication flow
- Tests fiscal code and VAT number operations
- Interactive testing mode available

✅ **Validation**
- Ensures token format correctness
- Validates API responses
- Comprehensive error handling

## Usage Examples

### Generate Token and Test Fiscal Code

```bash
# 1. Generate token
npm run token

# 2. Test fiscal code validation
curl -X POST http://localhost:8000/fiscal-code/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat .token)" \
  -d '{"code": "CCCFBA85D03L219P"}'
```

### Interactive Testing

```bash
node test-api.js --interactive
```

This provides a CLI menu to test specific endpoints with custom data.

## Configuration

The application reads from your `.env` file in the project root:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
```

## API Endpoints Tested

- `GET /health` - Health check (public)
- `GET /` - Web interface (public) 
- `POST /fiscal-code/validate` - Validate fiscal code
- `POST /fiscal-code/encode` - Generate fiscal code
- `POST /fiscal-code/decode` - Parse fiscal code
- `POST /vat/validate` - Validate VAT number
- `POST /vat/encode` - Generate VAT number
- `POST /vat/decode` - Parse VAT number

## Troubleshooting

### "No Clerk publishable key found"
- Ensure `.env` file exists in the project root (not in frontend/)
- Verify `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set
- Check key format: `pk_test_{instance_id}_{random}`

### "API Connection Errors"  
- Ensure Python FastAPI server is running on http://localhost:8000
- Start server: `cd .. && uv run python -m codicefiscale.__main_api__`

### "Token Expired"
- Tokens expire after 24 hours
- Generate new token: `npm run token`

## Integration with Python Backend

This frontend tool is designed to work with the main Python application:

```
project-root/
├── codicefiscale/           # Python FastAPI backend
├── frontend/               # Node.js token generator (this folder)  
├── tests/                  # Python tests
├── .env                    # Shared environment config
├── pyproject.toml         # Python dependencies
└── README.md              # Main project documentation
```

The Python backend must be running for the token generator tests to work:

```bash
# Start Python server (from project root)
uv run python -m codicefiscale.__main_api__

# Then use frontend tools (from frontend/)
cd frontend
npm run test-api
```

## Security Notes

⚠️ **TESTING ONLY**: These tokens are for development/testing purposes only:

- JWT signature verification is disabled in the Python API
- Tokens contain mock user data  
- Not suitable for production use
- For production, implement proper Clerk authentication flow

## Development Workflow

1. **Start Python API** (from project root):
   ```bash
   uv run python -m codicefiscale.__main_api__
   ```

2. **Generate test token** (from frontend/):
   ```bash
   npm run token
   ```

3. **Run API tests**:
   ```bash
   npm run test-api
   ```

4. **Interactive testing**:
   ```bash
   node test-api.js --interactive
   ```

For detailed documentation, see [CLERK_TOKEN_GENERATOR.md](CLERK_TOKEN_GENERATOR.md).