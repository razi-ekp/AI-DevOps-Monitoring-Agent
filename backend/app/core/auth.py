"""
API key authentication for FastAPI.
"""
import os

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header), request: Request = None):
    """Verify API key from X-API-Key header."""
    if request is not None and request.url.path == "/metrics":
        return None

    expected_key = os.getenv("API_SECRET_KEY", "").strip()
    if not expected_key:
        # If no key is configured, allow all requests (for development)
        return None

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    return api_key
