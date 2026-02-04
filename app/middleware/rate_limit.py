"""
Rate limiting middleware using SlowAPI.
Protects the API from abuse and ensures fair usage.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request

# Create limiter instance with IP-based rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute per IP
    storage_uri=None  # In-memory storage (use Redis URI for distributed)
)


# Rate limit decorators for different endpoint types
def rate_limit_auth(limit: str = "10/minute"):
    """Stricter rate limit for auth endpoints (login/register)."""
    return limiter.limit(limit)


def rate_limit_standard(limit: str = "60/minute"):
    """Standard rate limit for regular endpoints."""
    return limiter.limit(limit)


def rate_limit_heavy(limit: str = "20/minute"):
    """Rate limit for resource-intensive endpoints (checkout, etc)."""
    return limiter.limit(limit)


def setup_rate_limiting(app):
    """Configure rate limiting on the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
