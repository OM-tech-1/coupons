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
CACHE_TTL_DAY = 86400      # 24 hours


# ============== Redis Data Structure Helpers ==============

def redis_zincrby(key: str, member: str, amount: float = 1.0, ttl: int = None) -> Optional[float]:
    """Increment a member's score in a sorted set (for trending)."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        score = client.zincrby(key, amount, member)
        if ttl:
            client.expire(key, ttl)
        return score
    except Exception as e:
        logger.warning(f"Redis ZINCRBY error: {e}")
        return None


def redis_zrevrange(key: str, start: int = 0, stop: int = 9, withscores: bool = False) -> list:
    """Get top members from a sorted set in descending order."""
    client = get_redis_client()
    if client is None:
        return []
    try:
        return client.zrevrange(key, start, stop, withscores=withscores)
    except Exception as e:
        logger.warning(f"Redis ZREVRANGE error: {e}")
        return []


def redis_lpush_capped(key: str, value: str, max_length: int = 20, ttl: int = None) -> bool:
    """Push to a list and trim to max length (for recently viewed)."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        # Remove existing occurrence to avoid duplicates
        client.lrem(key, 0, value)
        # Push to front
        client.lpush(key, value)
        # Trim to max length
        client.ltrim(key, 0, max_length - 1)
        if ttl:
            client.expire(key, ttl)
        return True
    except Exception as e:
        logger.warning(f"Redis LPUSH error: {e}")
        return False


def redis_lrange(key: str, start: int = 0, stop: int = -1) -> list:
    """Get a range of items from a list."""
    client = get_redis_client()
    if client is None:
        return []
    try:
        return client.lrange(key, start, stop)
    except Exception as e:
        logger.warning(f"Redis LRANGE error: {e}")
        return []


def redis_hget(key: str, field: str) -> Optional[str]:
    """Get a field from a hash."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.hget(key, field)
    except Exception as e:
        logger.warning(f"Redis HGET error: {e}")
        return None


def redis_hset(key: str, field: str, value: str) -> bool:
    """Set a field in a hash."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.hset(key, field, value)
        return True
    except Exception as e:
        logger.warning(f"Redis HSET error: {e}")
        return False


def redis_hincrby(key: str, field: str, amount: int = -1) -> Optional[int]:
    """Increment/decrement a hash field value (for stock tracking)."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.hincrby(key, field, amount)
    except Exception as e:
        logger.warning(f"Redis HINCRBY error: {e}")
        return None
