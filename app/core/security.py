import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, this should be fetched from a secure vault or database.
# For demonstration, we allow multiple valid tokens via comma-separated string or a default.
VALID_API_KEYS = os.getenv("VALID_API_KEYS", "sk_test_123456789").split(",")


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to check if the provided API Key is valid.
    Applied to sensitive routes.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
