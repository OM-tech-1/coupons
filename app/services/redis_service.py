"""
Redis-powered frontend service for user experience features.
Uses Redis data structures (sorted sets, lists, hashes) for real-time features.
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.models.coupon import Coupon
from app.cache import (
    get_cache, set_cache, cache_key,
    redis_zincrby, redis_zrevrange,
    redis_lpush_capped, redis_lrange,
    redis_hget, redis_hset, redis_hincrby,
    CACHE_TTL_SHORT, CACHE_TTL_MEDIUM, CACHE_TTL_DAY
)


class RedisService:
    
    # ============== Trending Coupons ==============
    
    TRENDING_KEY_24H = "trending:coupons:24h"
    TRENDING_KEY_7D = "trending:coupons:7d"
    
    @staticmethod
    def record_trending_view(coupon_id: str):
        """Increment trending score when a coupon is viewed."""
        redis_zincrby(RedisService.TRENDING_KEY_24H, coupon_id, 1.0, ttl=CACHE_TTL_DAY)
        redis_zincrby(RedisService.TRENDING_KEY_7D, coupon_id, 1.0, ttl=CACHE_TTL_DAY * 7)
    
    @staticmethod
    def get_trending_coupons(db: Session, period: str = "24h", limit: int = 10) -> list:
        """Get top trending coupons by view count."""
        key = RedisService.TRENDING_KEY_24H if period == "24h" else RedisService.TRENDING_KEY_7D
        
        # Get top coupon IDs with scores from Redis sorted set
        trending_data = redis_zrevrange(key, 0, limit - 1, withscores=True)
        
        if not trending_data:
            # Fallback: return most recently created active coupons
            coupons = db.query(Coupon).filter(
                Coupon.is_active == True
            ).order_by(Coupon.created_at.desc()).limit(limit).all()
            return [RedisService._coupon_to_dict(c, 0) for c in coupons]
        
        # Fetch full coupon details from DB for the trending IDs
        result = []
        for coupon_id_str, score in trending_data:
            try:
                coupon = db.query(Coupon).filter(Coupon.id == coupon_id_str).first()
                if coupon and coupon.is_active:
                    result.append(RedisService._coupon_to_dict(coupon, int(score)))
            except Exception:
                continue
        
        return result
    
    # ============== Recently Viewed ==============
    
    @staticmethod
    def record_recently_viewed(session_id: str, coupon_id: str):
        """Add a coupon to the user's recently viewed list."""
        key = f"recently_viewed:{session_id}"
        redis_lpush_capped(key, coupon_id, max_length=20, ttl=CACHE_TTL_DAY * 30)
    
    @staticmethod
    def get_recently_viewed(db: Session, session_id: str, limit: int = 20) -> list:
        """Get recently viewed coupons for a session/user."""
        key = f"recently_viewed:{session_id}"
        coupon_ids = redis_lrange(key, 0, limit - 1)
        
        if not coupon_ids:
            return []
        
        # Fetch coupons in order
        result = []
        for coupon_id_str in coupon_ids:
            try:
                coupon = db.query(Coupon).filter(Coupon.id == coupon_id_str).first()
                if coupon:
                    result.append(RedisService._coupon_to_dict(coupon, 0))
            except Exception:
                continue
        
        return result
    
    # ============== Featured Coupons ==============
    
    @staticmethod
    def get_featured_coupons(db: Session, limit: int = 10) -> list:
        """Get featured coupons (cached for fast homepage loading)."""
        cache_k = cache_key("coupons", "featured", limit)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        coupons = db.query(Coupon).filter(
            Coupon.is_featured == True,
            Coupon.is_active == True
        ).order_by(Coupon.created_at.desc()).limit(limit).all()
        
        result = [RedisService._coupon_to_dict(c, 0) for c in coupons]
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
    
    # ============== Real-time Stock ==============
    
    STOCK_KEY = "coupon_stock"
    
    @staticmethod
    def init_stock(coupon_id: str, stock: int):
        """Initialize or update stock count in Redis."""
        redis_hset(RedisService.STOCK_KEY, coupon_id, str(stock))
    
    @staticmethod
    def get_stock(db: Session, coupon_id: str) -> dict:
        """Get real-time stock count (Redis first, DB fallback)."""
        # Try Redis first
        stock_str = redis_hget(RedisService.STOCK_KEY, coupon_id)
        if stock_str is not None:
            return {"coupon_id": coupon_id, "stock": int(stock_str), "source": "realtime"}
        
        # Fallback to DB
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return None
        
        stock = coupon.stock if coupon.stock is not None else -1  # -1 = unlimited
        # Cache in Redis for next time
        redis_hset(RedisService.STOCK_KEY, coupon_id, str(stock))
        return {"coupon_id": coupon_id, "stock": stock, "source": "database"}
    
    @staticmethod
    def decrement_stock(coupon_id: str) -> Optional[int]:
        """Decrement stock by 1 (called on claim/purchase)."""
        return redis_hincrby(RedisService.STOCK_KEY, coupon_id, -1)
    
    # ============== Helper ==============
    
    @staticmethod
    def _coupon_to_dict(coupon: Coupon, trending_score: int) -> dict:
        """Convert a Coupon model to a serializable dict."""
        return {
            "id": str(coupon.id),
            "code": coupon.code,
            "brand": coupon.brand,
            "title": coupon.title,
            "description": coupon.description,
            "discount_type": coupon.discount_type,
            "discount_amount": coupon.discount_amount,
            "price": coupon.price,
            "stock": coupon.stock,
            "is_featured": coupon.is_featured,
            "is_active": coupon.is_active,
            "expiration_date": str(coupon.expiration_date) if coupon.expiration_date else None,
            "created_at": str(coupon.created_at) if coupon.created_at else None,
            "category_id": str(coupon.category_id) if coupon.category_id else None,
            "availability_type": coupon.availability_type,
            "trending_score": trending_score,
        }
