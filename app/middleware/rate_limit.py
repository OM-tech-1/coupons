"""
Rate limiting middleware using SlowAPI.
Protects the API from abuse and ensures fair usage.
"""
import os
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Test Redis connectivity before using it for rate limiting
REDIS_URL = os.getenv("REDIS_URL")
_storage_uri = None

if REDIS_URL:
    try:
        import redis
        r = redis.from_url(REDIS_URL, socket_connect_timeout=3)
        r.ping()
        _storage_uri = REDIS_URL
        logger.info("Rate limiter using Redis storage")
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiter ({e}), using in-memory storage")
        _storage_uri = None

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=_storage_uri
)


# Rate limit decorators for different endpoint types
def rate_limit_auth(limit: str = "10/minute"):
    return limiter.limit(limit)


def rate_limit_standard(limit: str = "60/minute"):
    return limiter.limit(limit)


def rate_limit_heavy(limit: str = "20/minute"):
    return limiter.limit(limit)


def _custom_rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle rate limit errors gracefully, including Redis auth failures."""
    detail = getattr(exc, "detail", str(exc))
    return JSONResponse(
        {"error": f"Rate limit exceeded: {detail}"},
        status_code=429
    )


def setup_rate_limiting(app):
    """Configure rate limiting on the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
