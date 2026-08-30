from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Use Redis for rate limiting if configured, otherwise falls back to memory
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
