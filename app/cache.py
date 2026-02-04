"""
Redis caching layer for high-load performance optimization.
Provides caching for frequently accessed data like coupon listings.
"""
import os
import json
from typing import Optional, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Redis connection (lazy initialization)
_redis_client = None

def get_redis_client():
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client


def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    return None


def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """Set a value in cache with TTL (default 5 minutes)."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
        return False


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache keys matching a pattern."""
    client = get_redis_client()
    if client is None:
        return 0
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")
    return 0


def cache_key(*args) -> str:
    """Build a cache key from arguments."""
    return ":".join(str(arg) for arg in args)


# Cache TTL constants (in seconds)
CACHE_TTL_SHORT = 60       # 1 minute
CACHE_TTL_MEDIUM = 300     # 5 minutes
CACHE_TTL_LONG = 3600      # 1 hour
