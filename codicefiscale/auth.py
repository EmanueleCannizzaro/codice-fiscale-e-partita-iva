from __future__ import annotations

import os
from typing import Any, Optional

try:
    import jwt
    from dotenv import load_dotenv
    from fastapi import Depends, HTTPException, Request
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    
    # Load environment variables from .env file
    load_dotenv()
except ImportError as e:
    raise ImportError(
        "Authentication dependencies not installed. "
        "Install with: pip install 'python-codicefiscale[api]'"
    ) from e


class ClerkAuth:
    """Clerk authentication handler for FastAPI."""
    
    def __init__(self, publishable_key: Optional[str] = None, secret_key: Optional[str] = None):
        # Try both environment variable names for publishable key
        # Filter out empty strings
        def _get_non_empty_env(key: str) -> Optional[str]:
            value = os.getenv(key)
            return value if value and value.strip() else None
        
        self.publishable_key = (
            publishable_key 
            or _get_non_empty_env("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
            or _get_non_empty_env("CLERK_PUBLISHABLE_KEY")
        )
        
        self.secret_key = secret_key or os.getenv("CLERK_SECRET_KEY") or None
        
        if not self.publishable_key:
            raise ValueError(
                "Clerk publishable key not found. "
                "Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY or CLERK_PUBLISHABLE_KEY environment variable."
            )
        
        # Extract the instance ID from the publishable key
        # Format: pk_test_<instance_id>_<random> or pk_live_<instance_id>_<random>
        parts = self.publishable_key.split("_")
        if len(parts) < 3:
            raise ValueError("Invalid Clerk publishable key format")
        
        self.instance_id = parts[2]
        self.jwks_url = f"https://{self.instance_id}.clerk.accounts.dev/.well-known/jwks.json"
        
    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a Clerk JWT token."""
        try:
            # For production, you should fetch and cache the JWKS
            # For this example, we'll decode without verification (NOT RECOMMENDED FOR PRODUCTION)
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},  # DANGER: Only for demo!
                algorithms=["RS256"]
            )
            
            # Validate basic token structure
            if "sub" not in decoded:
                raise ValueError("Token missing subject claim")
            
            if "iss" not in decoded:
                raise ValueError("Token missing issuer claim")
            
            # Validate issuer matches Clerk instance
            expected_issuer = f"https://{self.instance_id}.clerk.accounts.dev"
            if decoded["iss"] != expected_issuer:
                raise ValueError(f"Invalid issuer. Expected {expected_issuer}")
            
            return decoded
            
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}") from e
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e


def create_clerk_dependency(auto_error: bool = True):
    """Create a Clerk authentication dependency function."""
    clerk_auth = ClerkAuth()
    bearer = HTTPBearer(auto_error=auto_error)
    
    async def clerk_dependency(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict[str, Any]:
        if credentials is None:
            if auto_error:
                raise HTTPException(
                    status_code=401, 
                    detail="Authorization header required"
                )
            return {}
        
        if credentials.scheme.lower() != "bearer":
            if auto_error:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid authentication scheme"
                )
            return {}
        
        return clerk_auth.verify_token(credentials.credentials)
    
    return clerk_dependency


# Global authentication dependencies - only create if credentials are available
try:
    # Check if credentials exist before creating dependencies
    def _get_non_empty_env(key: str) -> Optional[str]:
        value = os.getenv(key)
        return value if value and value.strip() else None
    
    if (_get_non_empty_env("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY") or 
        _get_non_empty_env("CLERK_PUBLISHABLE_KEY")):
        clerk_auth = create_clerk_dependency(auto_error=True)
        optional_clerk_auth = create_clerk_dependency(auto_error=False)
    else:
        # Create dummy dependencies when no credentials
        def dummy_auth() -> dict[str, Any]:
            return {}
        clerk_auth = dummy_auth
        optional_clerk_auth = dummy_auth
except (ValueError, ImportError):
    # Fallback to dummy dependencies if initialization fails
    def dummy_auth() -> dict[str, Any]:
        return {}
    clerk_auth = dummy_auth
    optional_clerk_auth = dummy_auth


def get_user_id(auth_data: dict[str, Any]) -> Optional[str]:
    """Extract user ID from Clerk auth data."""
    return auth_data.get("sub")


def get_user_email(auth_data: dict[str, Any]) -> Optional[str]:
    """Extract user email from Clerk auth data."""
    return auth_data.get("email")


def get_user_metadata(auth_data: dict[str, Any]) -> dict[str, Any]:
    """Extract user metadata from Clerk auth data."""
    return {
        "user_id": get_user_id(auth_data),
        "email": get_user_email(auth_data),
        "name": auth_data.get("name"),
        "given_name": auth_data.get("given_name"),
        "family_name": auth_data.get("family_name"),
        "created_at": auth_data.get("created_at"),
        "updated_at": auth_data.get("updated_at"),
    }