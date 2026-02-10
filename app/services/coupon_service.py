from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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
        from app.models.coupon_country import CouponCountry
        
        # Extract country_ids before creating coupon
        country_ids = coupon_data.country_ids
        
        db_coupon = Coupon(
            code=coupon_data.code.upper(),
            redeem_code=coupon_data.redeem_code,
            brand=coupon_data.brand,
            title=coupon_data.title,
            description=coupon_data.description,
            discount_type=coupon_data.discount_type,
            discount_amount=coupon_data.discount_amount,
            min_purchase=coupon_data.min_purchase,
            max_uses=coupon_data.max_uses,
            expiration_date=coupon_data.expiration_date,
            category_id=coupon_data.category_id,
            availability_type=coupon_data.availability_type,
            price=coupon_data.price,
            stock=coupon_data.stock,
            is_featured=coupon_data.is_featured,
        )
        db.add(db_coupon)
        db.flush()  # Flush to get the coupon ID
        
        # Create country associations
        for country_id in country_ids:
            association = CouponCountry(coupon_id=db_coupon.id, country_id=country_id)
            db.add(association)
        
        db.commit()
        db.refresh(db_coupon)
        
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
        region_id: Optional[UUID] = None,
        country_id: Optional[UUID] = None,
        availability_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Coupon]:
        """Get all coupons with optional filtering (cached)"""
        from sqlalchemy.orm import joinedload
        from app.models.coupon_country import CouponCountry
        from app.models.country import Country
        
        # Try cache first (with new filter parameters in cache key)
        cache_k = cache_key("coupons", "list", skip, limit, active_only, 
                           str(category_id) if category_id else "none",
                           str(region_id) if region_id else "none",
                           str(country_id) if country_id else "none",
                           availability_type or "all",
                           search or "none")
        cached = get_cache(cache_k)
        if cached is not None:
            # Return cached data (already serialized)
            return cached
        
        # Query database with eager loading for relationships
        query = db.query(Coupon).options(
            joinedload(Coupon.category),
            joinedload(Coupon.country_associations).joinedload(CouponCountry.country)
        )
        
        # Apply filters
        if active_only:
            query = query.filter(Coupon.is_active == True)
        
        if category_id:
            query = query.filter(Coupon.category_id == category_id)
        
        if availability_type:
            query = query.filter(Coupon.availability_type == availability_type)
        
        # Filter by country (requires join)
        if country_id:
            query = query.join(CouponCountry).filter(CouponCountry.country_id == country_id)
        
        # Filter by region (requires joins through country)
        if region_id:
            query = query.join(CouponCountry).join(Country).filter(Country.region_id == region_id)
        
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
        
        # Cache the result (serialize for caching)
        cache_data = [
            {
                "id": str(c.id),
                "code": c.code,
                "redeem_code": c.redeem_code,
                "brand": c.brand,
                "title": c.title,
                "description": c.description,
                "discount_type": c.discount_type,
                "discount_amount": c.discount_amount,
                "min_purchase": c.min_purchase,
                "max_uses": c.max_uses,
                "current_uses": c.current_uses,
                "expiration_date": str(c.expiration_date) if c.expiration_date else None,
                "is_active": c.is_active,
                "price": c.price,
                "stock": c.stock,
                "is_featured": c.is_featured,
                "created_at": str(c.created_at) if c.created_at else None,
                "category_id": str(c.category_id) if c.category_id else None,
                "availability_type": c.availability_type,
            }
            for c in coupons
        ]
        set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        return coupons

    @staticmethod
    def get_by_id(db: Session, coupon_id: UUID) -> Optional[Coupon]:
        """Get a coupon by its ID"""
        return db.query(Coupon).filter(Coupon.id == coupon_id).first()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Coupon]:
        """Get a coupon by its code"""
        return db.query(Coupon).filter(Coupon.code == code.upper()).first()

    @staticmethod
    def update(db: Session, coupon_id: UUID, coupon_data: CouponUpdate) -> Optional[Coupon]:
        """Update a coupon"""
        from app.models.coupon_country import CouponCountry
        
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return None
        
        update_data = coupon_data.model_dump(exclude_unset=True)
        
        # Handle country_ids separately
        country_ids = update_data.pop('country_ids', None)
        
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper()
        
        for field, value in update_data.items():
            setattr(db_coupon, field, value)
        
        # Update country associations if country_ids provided
        if country_ids is not None:
            # Remove existing associations
            db.query(CouponCountry).filter(CouponCountry.coupon_id == coupon_id).delete()
            # Add new associations
            for country_id in country_ids:
                association = CouponCountry(coupon_id=coupon_id, country_id=country_id)
                db.add(association)
        
        db.commit()
        db.refresh(db_coupon)
        
        # Invalidate coupon caches
        invalidate_cache("coupons:list:*")
        invalidate_cache(f"coupons:id:{coupon_id}")
        
        return db_coupon

    @staticmethod
    def delete(db: Session, coupon_id: UUID) -> bool:
        """Delete a coupon and all related records"""
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return False
        
        # Delete related records that have NOT NULL foreign keys
        from app.models.user_coupon import UserCoupon
        from app.models.coupon_view import CouponView
        db.query(UserCoupon).filter(UserCoupon.coupon_id == coupon_id).delete()
        db.query(CouponView).filter(CouponView.coupon_id == coupon_id).delete()
        
        db.delete(db_coupon)
        db.commit()
        
        # Invalidate coupon caches
        invalidate_cache("coupons:list:*")
        invalidate_cache(f"coupons:id:{coupon_id}")
        
        return True

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
