# Quick Authentication Setup

This is a condensed guide for setting up Clerk authentication with the python-codicefiscale API. For the complete guide, see [AUTHENTICATION.md](AUTHENTICATION.md).

## 🚀 Quick Start (5 minutes)

### 1. Get Clerk Credentials
1. Create account at [clerk.com](https://clerk.com)
2. Create new application
3. Copy your keys from the dashboard

### 2. Configure Environment
```bash
# Create .env file
cat > .env << EOF
CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_secret_here
EOF
```

### 3. Start Server
```bash
# Install dependencies
uv sync --extra api

# Start server
uv run python -m codicefiscale.__main_api__
```

### 4. Test Authentication Status
Visit [http://localhost:8000](http://localhost:8000) - you should see:
- ✅ "Authentication is **enabled**"
- ⚠️ Warning about no active session

## 🔑 Getting JWT Token for API Calls

### Method 1: From Frontend App
```javascript
const { getToken } = useAuth(); // Clerk React hook
const token = await getToken();
```

### Method 2: Test Token (Development Only)
```python
import jwt
from datetime import datetime, timedelta

# Extract instance ID from your publishable key
publishable_key = "pk_test_instance123_randomstring"
instance_id = publishable_key.split('_')[2]

# Create test JWT (signature verification is disabled in demo)
payload = {
    'sub': 'user_test123',
    'iss': f'https://{instance_id}.clerk.accounts.dev',
    'email': 'test@example.com',
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}

token = jwt.encode(payload, 'secret', algorithm='HS256')
print(f"Test token: {token}")
```

## 📡 Using the API

### With Authentication:
```bash
curl -X POST "http://localhost:8000/fiscal-code/validate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "CCCFBA85D03L219P"}'
```

### Without Authentication (for testing):
```bash
# Disable auth by clearing env vars
CLERK_PUBLISHABLE_KEY="" uv run python -m codicefiscale.__main_api__

# Then call API directly
curl -X POST "http://localhost:8000/fiscal-code/validate" \
  -H "Content-Type: application/json" \
  -d '{"code": "CCCFBA85D03L219P"}'
```

## 🔍 Troubleshooting

### Getting 403 Forbidden?
- ✅ Check JWT token is included: `Authorization: Bearer <token>`
- ✅ Verify token hasn't expired
- ✅ Ensure instance ID matches your Clerk app

### Authentication unexpectedly disabled?
- ✅ Check environment variables are set: `echo $CLERK_PUBLISHABLE_KEY`
- ✅ Verify .env file exists and is loaded
- ✅ Run diagnostic: `python test_clerk_auth.py`

### Web interface showing warnings?
- ✅ With auth enabled but no user session, you'll see setup instructions
- ✅ This is normal - the web interface can't automatically get JWT tokens
- ✅ Use direct API calls with proper tokens instead

## 📚 Next Steps

- [Full Authentication Guide](AUTHENTICATION.md) - Complete setup instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Health Check](http://localhost:8000/health) - Server status
- [Test Script](test_clerk_auth.py) - Diagnostic tool

---

**Security Note**: The current implementation has JWT signature verification disabled for demo purposes. Enable proper JWKS verification for production use.