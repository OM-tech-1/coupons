from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM


class CouponService:
    
    @staticmethod
    def create(db: Session, coupon_data: CouponCreate) -> Coupon:
        """Create a new coupon"""
        # Extract non-model data before creating coupon
        import logging
        
        db_coupon = Coupon(
            code=coupon_data.code.upper(),
            redeem_code=coupon_data.redeem_code,
            brand=coupon_data.brand,
            title=coupon_data.title,
            description=coupon_data.description,
            discount_type=coupon_data.discount_type,
            discount_amount=coupon_data.discount_amount,
            max_uses=coupon_data.max_uses,
            expiration_date=coupon_data.expiration_date,
            category_id=coupon_data.category_id,
            stock=coupon_data.stock,
            is_featured=coupon_data.is_featured,
            picture_url=coupon_data.picture_url,
            pricing=coupon_data.pricing,
        )
        db.add(db_coupon)
        db.flush()  # Flush to get the coupon ID
        
        db.commit()
        db.refresh(db_coupon)  # Refresh to get database-generated fields (created_at, etc.)
        
        # Invalidate coupon list cache
        invalidate_cache("coupons:list:*")
        
        return db_coupon


    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category_id: Optional[UUID] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
        min_discount: Optional[float] = None,
    ) -> List[Coupon]:
        """Get all coupons with optional filtering"""
        # Query database with eager loading for relationships (avoid N+1)
        query = db.query(Coupon).options(
            joinedload(Coupon.category)
        )
        
        # Apply filters
        if active_only:
            query = query.filter(Coupon.is_active == True)
        
        # Exclude package coupons from regular listings
        query = query.filter(Coupon.is_package_coupon == False)
        
        if category_id:
            query = query.filter(Coupon.category_id == category_id)
        
        if is_featured is not None:
            query = query.filter(Coupon.is_featured == is_featured)

        if min_discount is not None:
            query = query.filter(Coupon.discount_amount >= min_discount)
        
        # Search by title or brand (case-insensitive)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    func.lower(Coupon.title).like(func.lower(search_term)),
                    func.lower(Coupon.brand).like(func.lower(search_term)),
                    func.lower(Coupon.code).like(func.lower(search_term))
                )
            )
        
        coupons = query.offset(skip).limit(limit).all()
        
        return coupons

    @staticmethod
    def get_by_id(db: Session, coupon_id: UUID) -> Optional[Coupon]:
        """Get a coupon by its ID (cached)"""
        # Helper for sanitization
        def sanitize(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except UnicodeDecodeError:
                    return None
            return val

        from sqlalchemy.orm import joinedload
        
        cache_k = cache_key("coupons", "id", str(coupon_id))
        cached = get_cache(cache_k)
        if cached is not None:
            # Reconstruct object
            c_obj = Coupon(**{k: v for k, v in cached.items() if k not in ['category', 'pricing']})
            c_obj.pricing = cached.get('pricing')
            
            if cached.get('category'):
                from app.models.category import Category
                c_obj.category = Category(**cached['category'])
            
            return c_obj
        
        coupon = db.query(Coupon).options(
            joinedload(Coupon.category)
        ).filter(Coupon.id == coupon_id).first()
        
        if coupon:
            set_cache(cache_k, {
                "id": str(coupon.id), 
                "code": sanitize(coupon.code), 
                "redeem_code": sanitize(coupon.redeem_code),
                "brand": sanitize(coupon.brand), 
                "title": sanitize(coupon.title), 
                "description": sanitize(coupon.description),
                "discount_type": sanitize(coupon.discount_type), 
                "discount_amount": coupon.discount_amount,
                "max_uses": coupon.max_uses,
                "current_uses": coupon.current_uses, 
                "is_active": coupon.is_active,
                "stock": coupon.stock, 
                "is_featured": coupon.is_featured,
                "created_at": str(coupon.created_at) if coupon.created_at else None,
                "expiration_date": str(coupon.expiration_date) if coupon.expiration_date else None,
                "category_id": str(coupon.category_id) if coupon.category_id else None,
                "category": {"id": str(coupon.category.id), "name": sanitize(coupon.category.name), "slug": sanitize(coupon.category.slug)} if coupon.category else None,
                "picture_url": sanitize(coupon.picture_url),
                "pricing": coupon.pricing,
            }, CACHE_TTL_MEDIUM)
            
        return coupon

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Coupon]:
        """Get a coupon by its code (cached)"""
        # Helper for sanitization
        def sanitize(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except UnicodeDecodeError:
                    return None
            return val

        upper_code = code.upper()
        cache_k = cache_key("coupons", "code", upper_code)
        cached = get_cache(cache_k)
        if cached is not None:
            c_obj = Coupon(**{k: v for k, v in cached.items() if k not in ['pricing']})
            c_obj.pricing = cached.get('pricing')
            return c_obj
        
        coupon = db.query(Coupon).filter(Coupon.code == upper_code).first()
        if coupon:
            set_cache(cache_k, {
                "id": str(coupon.id), 
                "code": sanitize(coupon.code), 
                "title": sanitize(coupon.title), 
                "picture_url": sanitize(coupon.picture_url),
                "pricing": coupon.pricing,
                "discount_amount": coupon.discount_amount
            }, CACHE_TTL_MEDIUM)
            
        return coupon

    @staticmethod
    def update(db: Session, coupon_id: UUID, coupon_data: CouponUpdate) -> Optional[Coupon]:
        """Update a coupon"""
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return None
            
        update_data = coupon_data.model_dump(exclude_unset=True)
        
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper()
        
        for field, value in update_data.items():
            setattr(db_coupon, field, value)
        
        db.commit()
        db.refresh(db_coupon)  # Refresh to get updated relationships
        
        # Invalidate coupon caches
        invalidate_cache("coupons:list:*")
        invalidate_cache(f"coupons:id:{coupon_id}")
        
        return db_coupon

    @staticmethod
    def delete(db: Session, coupon_id: UUID) -> bool:
        """Soft-delete a coupon to preserve order history and cart references."""
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return False
            
        # We never hard delete coupons because they might be referenced in 
        # cart items, orders, or user wallets. We only soft-delete them.
        db_coupon.is_active = False
        db_coupon.is_featured = False
        db.commit()
        
        # Invalidate coupon caches
        invalidate_cache("coupons:list:*")
        invalidate_cache(f"coupons:id:{coupon_id}")
        
        return True

    @staticmethod
    def get_price(coupon: Coupon, currency: str = "USD") -> float:
        """Get the price of a coupon for a specific currency from pricing JSON"""
        if not coupon or not coupon.pricing:
            return 0.0
        
        # Try to get currency-specific price
        currency_data = coupon.pricing.get(currency.upper())
        if currency_data is not None:
            if isinstance(currency_data, dict) and "price" in currency_data:
                return float(currency_data["price"])
            elif isinstance(currency_data, (int, float)):
                return float(currency_data)
            
        # Fallback to USD if requested currency not found
        if currency.upper() != "USD":
            usd_data = coupon.pricing.get("USD")
            if usd_data is not None:
                if isinstance(usd_data, dict) and "price" in usd_data:
                    return float(usd_data["price"])
                elif isinstance(usd_data, (int, float)):
                    return float(usd_data)
                
        return 0.0

    @staticmethod
    def is_valid(coupon: Coupon) -> tuple[bool, str]:
        """Check if a coupon is valid for use"""
        if not coupon.is_active:
            return False, "Coupon is not active"
        
        if coupon.expiration_date and coupon.expiration_date < datetime.utcnow():
            return False, "Coupon has expired"
        
        if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
            return False, "Coupon usage limit reached"
        
        return True, "Coupon is valid"

    @staticmethod
    def increment_usage(db: Session, coupon_id: UUID, quantity: int = 1) -> bool:
        """
        Atomically increment usage count and decrement stock.
        Returns True if successful, False if limits reached (race condition).
        """
        # We use a direct UPDATE statement with WHERE clause to ensure atomicity
        # and prevent race conditions (DB-level locking)
        
        # 1. Update current_uses (Check max_uses)
        # 2. Update stock (Check stock > 0)
        
        # Note: We need to handle them carefully.
        # If stock is None, it's unlimited stock.
        # If max_uses is None, it's unlimited uses.
        
        # Let's fetch the coupon first to check structure, but update via query
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).with_for_update().first()
        if not coupon:
            return False
            
        # Check limits
        if coupon.max_uses is not None and (coupon.current_uses + quantity) > coupon.max_uses:
            return False
            
        if coupon.stock is not None:
             if coupon.stock < quantity:
                 return False
             coupon.stock -= quantity
             
        coupon.current_uses += quantity
        
        db.commit()
        
        # Invalidate cache
        invalidate_cache(f"coupons:id:{coupon_id}")
        invalidate_cache("coupons:list:*")
        
        return True
