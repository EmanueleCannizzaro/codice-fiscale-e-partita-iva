# Clerk JWT Token Generator

This Node.js application generates valid JWT tokens for testing the Python FastAPI application with Clerk authentication.

## Features

- 🔐 **Generate JWT Tokens**: Creates valid JWT tokens compatible with your Clerk configuration
- 🧪 **API Testing**: Automated testing of all API endpoints
- 📋 **Interactive Mode**: Manual testing with custom inputs
- ✅ **Validation**: Ensures token format and structure are correct
- 💾 **Token Persistence**: Saves generated tokens for reuse

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Generate a JWT Token

```bash
npm run token
```

This will:
- Check your Clerk configuration from `.env` file
- Generate a valid JWT token
- Display usage examples
- Save the token to `.token` file

### 3. Test the API

```bash
npm run test-api
```

This will run a comprehensive test suite against your Python API:
- Health check endpoint
- Authentication-protected endpoints
- Fiscal code validation and encoding
- VAT number validation

### 4. Interactive Testing

```bash
node test-api.js --interactive
```

This provides an interactive CLI for testing specific endpoints with custom data.

## Usage Examples

### Generate Token and Test Fiscal Code

```bash
# 1. Generate token
npm run token

# 2. Use the token to test fiscal code validation
curl -X POST http://localhost:8000/fiscal-code/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat .token)" \
  -d '{"code": "CCCFBA85D03L219P"}'
```

### Test VAT Number Validation

```bash
curl -X POST http://localhost:8000/vat/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat .token)" \
  -d '{"partita_iva": "01234567897"}'
```

### Generate Fiscal Code

```bash
curl -X POST http://localhost:8000/fiscal-code/encode \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat .token)" \
  -d '{
    "lastname": "Rossi",
    "firstname": "Mario", 
    "gender": "M",
    "birthdate": "01/01/1990",
    "birthplace": "Milano"
  }'
```

## Configuration

The token generator reads configuration from your `.env` file:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
CLERK_JWKS_URL=https://your-instance.clerk.accounts.dev/.well-known/jwks.json
```

Required:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` or `CLERK_PUBLISHABLE_KEY`

Optional:
- `CLERK_SECRET_KEY` (not used by this generator but good to have)
- `API_BASE_URL` (defaults to http://localhost:8000)

## Scripts

- `npm run token` - Generate a new JWT token
- `npm run test-api` - Run automated API tests
- `npm start` - Alias for `npm run token`
- `node test-api.js --interactive` - Interactive testing mode

## Token Details

The generated tokens include:

### Standard JWT Claims
- `sub`: User ID (user_xxx)
- `iss`: Issuer (https://your-instance.clerk.accounts.dev)
- `aud`: Audience
- `exp`: Expiration time (24 hours)
- `iat`: Issued at time
- `nbf`: Not before time

### Clerk-Specific Claims
- `sid`: Session ID
- `email`: User email
- `name`: Full name
- `given_name`: First name
- `family_name`: Last name
- `email_verified`: Email verification status
- `picture`: Avatar URL
- `public_metadata`: Public user metadata
- `private_metadata`: Private user metadata

## Security Notes

⚠️ **IMPORTANT**: These tokens are for **TESTING ONLY**

- JWT signature verification is disabled in the Python API
- Tokens contain mock data
- Do not use in production environments
- For production, implement proper Clerk authentication flow

## Troubleshooting

### "No Clerk publishable key found"
- Ensure `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` or `CLERK_PUBLISHABLE_KEY` is set in `.env`
- Check that the key starts with `pk_test_` or `pk_live_`

### "Invalid publishable key format"
- Verify the key has the format: `pk_test_{instance_id}_{random}`
- Ensure the key is complete (not truncated)

### API Connection Errors
- Ensure the Python FastAPI server is running on http://localhost:8000
- Check that authentication dependencies are installed: `uv sync`

### Token Expired
- Tokens expire after 24 hours
- Generate a new token: `npm run token`

## Files Created

- `.token` - Saved JWT token for reuse
- `node_modules/` - Node.js dependencies
- `package-lock.json` - Dependency lock file

## API Testing Results

The test suite validates:

✅ Public endpoints work without authentication
✅ Protected endpoints reject requests without tokens
✅ Protected endpoints accept valid JWT tokens
✅ All CRUD operations for fiscal codes and VAT numbers
✅ Error handling for invalid data

Example output:
```
🧪 API Test Suite
==================================================
Running: Health Check (Public)
✅ Status: 200 (expected)

Running: Fiscal Code Validation (With Auth)  
✅ Status: 200 (expected)
Response: {
  "code": "CCCFBA85D03L219P",
  "valid": true,
  "details": { ... }
}

🧪 Test Results
==================================================
✅ Passed: 7
Total: 7
```