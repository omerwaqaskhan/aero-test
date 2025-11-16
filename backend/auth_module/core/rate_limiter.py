"""Rate limiting utilities using slowapi."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
from typing import Optional
from ..core.config import config

# Initialize Redis connection for rate limiting
try:
    redis_client = redis.from_url(config.redis_url, decode_responses=True)
    redis_client.ping()  # Test connection
    redis_available = True
except Exception:
    redis_available = False
    redis_client = None

# Create rate limiter
if redis_available:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=config.redis_url,
        default_limits=["1000/hour"]  # Global default limit
    )
else:
    # Fallback to in-memory storage if Redis unavailable
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000/hour"]
    )


def get_rate_limiter() -> Limiter:
    """Get rate limiter instance."""
    return limiter


# Rate limit decorator for endpoints
def rate_limit(limit: str):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @rate_limit("10/minute")
        async def my_endpoint(...):
            ...
    """
    return limiter.limit(limit)


# Custom rate limit exceeded handler
@limiter.limit("1000/hour")  # Prevent abuse of rate limit errors
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "retry_after": exc.retry_after,
                "timestamp": exc.reset_at.isoformat() if exc.reset_at else None
            }
        }
    )

