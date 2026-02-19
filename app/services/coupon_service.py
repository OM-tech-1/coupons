from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM
from app.utils.currency import get_currency_symbol


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
            picture_url=coupon_data.picture_url,
            pricing=coupon_data.pricing,
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
    def _apply_currency(coupon: Coupon, currency_code: str = "USD") -> Coupon:
        """Apply currency-specific pricing to coupon object"""
        # Set default symbol and code
        coupon.currency_symbol = get_currency_symbol("USD")
        coupon.currency = "USD"
        
        if not currency_code or currency_code == "USD":
            return coupon
            
        # Look for pricing override
        if coupon.pricing and currency_code in coupon.pricing:
            pricing_data = coupon.pricing[currency_code]
            coupon.price = pricing_data.get("price", coupon.price)
            coupon.discount_amount = pricing_data.get("discount_amount", coupon.discount_amount)
            coupon.currency_symbol = get_currency_symbol(currency_code)
            coupon.currency = currency_code
            
        return coupon

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
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
        min_discount: Optional[float] = None,
        currency_code: str = "USD"
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
                           search or "none",
                           str(is_featured) if is_featured is not None else "none",
                           str(min_discount) if min_discount is not None else "none")
        cached = get_cache(cache_k)
        cached = get_cache(cache_k)
        if cached is not None:
            # Reconstruct Coupon objects from cache and apply currency
            coupons = []
            for c_data in cached:
                # We need to reconstruct objects to be compatible with Pydantic from_attributes
                # OR we can return dicts if the API layer handles it.
                # Assuming API expects objects or dicts compatible with response model.
                
                # Let's use a dynamic object or simple class logic
                c_obj = Coupon(**{k: v for k, v in c_data.items() if k not in ['category', 'countries', 'pricing']})
                # Restore pricing for calculation
                c_obj.pricing = c_data.get('pricing')
                
                # Restore relationships manually if needed, or rely on dict access in schema
                # Pydantic's from_attributes works with objects having attributes.
                # To support validation, let's keep it simple: modify the Dict if possible 
                # OR modify the object.
                
                CouponService._apply_currency(c_obj, currency_code)
                
                # Restore relationship structures for schema
                if c_data.get('category'):
                    from app.models.category import Category
                    c_obj.category = Category(**c_data['category'])
                
                # For countries, it's a list of dicts. 
                # Schema expects c.country_associations which yield c.country
                # This is tricky with raw objects. 
                # Let's try to mimic the structure Expected by Pydantic.
                
                # Actually, simpler: modify c_data dict and return dicts?
                # But type hint says List[Coupon].
                # Let's stick to modifying the object.
                
                coupons.append(c_obj)
                
            return coupons
        
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
        
        if is_featured is not None:
            query = query.filter(Coupon.is_featured == is_featured)

        if min_discount is not None:
            query = query.filter(Coupon.discount_amount >= min_discount)
        
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
        def sanitize(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except UnicodeDecodeError:
                    return None
            return val

        cache_data = [
            {
                "id": str(c.id),
                "code": sanitize(c.code),
                "redeem_code": sanitize(c.redeem_code),
                "brand": sanitize(c.brand),
                "title": sanitize(c.title),
                "description": sanitize(c.description),
                "discount_type": sanitize(c.discount_type),
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
                "category": {"id": str(c.category.id), "name": sanitize(c.category.name), "slug": sanitize(c.category.slug)} if c.category else None,
                "availability_type": sanitize(c.availability_type),
                "picture_url": sanitize(c.picture_url),
                "pricing": c.pricing,
                "countries": [{"id": str(ca.country.id), "name": sanitize(ca.country.name), "slug": sanitize(ca.country.slug), "country_code": sanitize(ca.country.country_code)} for ca in c.country_associations] if c.country_associations else [],
            }
            for c in coupons
        ]
        set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        # Apply currency to live objects
        for c in coupons:
            CouponService._apply_currency(c, currency_code)
            
        return coupons

    @staticmethod
    def get_by_id(db: Session, coupon_id: UUID, currency_code: str = "USD") -> Optional[Coupon]:
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
        from app.models.coupon_country import CouponCountry
        
        cache_k = cache_key("coupons", "id", str(coupon_id))
        cached = get_cache(cache_k)
        cached = get_cache(cache_k)
        if cached is not None:
            # Reconstruct object
            c_obj = Coupon(**{k: v for k, v in cached.items() if k not in ['category', 'countries', 'pricing']})
            c_obj.pricing = cached.get('pricing')
            CouponService._apply_currency(c_obj, currency_code)
            
            if cached.get('category'):
                from app.models.category import Category
                c_obj.category = Category(**cached['category'])
            
            return c_obj
        
        coupon = db.query(Coupon).options(
            joinedload(Coupon.category),
            joinedload(Coupon.country_associations).joinedload(CouponCountry.country)
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
                "min_purchase": coupon.min_purchase, 
                "max_uses": coupon.max_uses,
                "current_uses": coupon.current_uses, 
                "is_active": coupon.is_active,
                "price": coupon.price, 
                "stock": coupon.stock, 
                "is_featured": coupon.is_featured,
                "created_at": str(coupon.created_at) if coupon.created_at else None,
                "expiration_date": str(coupon.expiration_date) if coupon.expiration_date else None,
                "category_id": str(coupon.category_id) if coupon.category_id else None,
                "category": {"id": str(coupon.category.id), "name": sanitize(coupon.category.name), "slug": sanitize(coupon.category.slug)} if coupon.category else None,
                "availability_type": sanitize(coupon.availability_type),
                "picture_url": sanitize(coupon.picture_url),
                "pricing": coupon.pricing,
                "countries": [{"id": str(ca.country.id), "name": sanitize(ca.country.name), "slug": sanitize(ca.country.slug), "country_code": sanitize(ca.country.country_code)} for ca in coupon.country_associations] if coupon.country_associations else [],
            }, CACHE_TTL_MEDIUM)
            
            CouponService._apply_currency(coupon, currency_code)
            
        return coupon

    @staticmethod
    def get_by_code(db: Session, code: str, currency_code: str = "USD") -> Optional[Coupon]:
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
             # Reconstruct
            c_obj = Coupon(**{k: v for k, v in cached.items() if k not in ['pricing']})
            c_obj.pricing = cached.get('pricing')
            CouponService._apply_currency(c_obj, currency_code)
            return c_obj
        
        coupon = db.query(Coupon).filter(Coupon.code == upper_code).first()
        if coupon:
            set_cache(cache_k, {
                "id": str(coupon.id), 
                "code": sanitize(coupon.code), 
                "title": sanitize(coupon.title), 
                "picture_url": sanitize(coupon.picture_url),
                "pricing": coupon.pricing,
                "discount_amount": coupon.discount_amount, "price": coupon.price
            }, CACHE_TTL_MEDIUM)
            CouponService._apply_currency(coupon, currency_code)
            
        return coupon

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
        """Delete a coupon. Soft-deletes if it has order history, hard-deletes otherwise."""
        from app.models.order import OrderItem
        from app.models.user_coupon import UserCoupon
        from app.models.coupon_view import CouponView
        
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return False
        
        # Check if coupon has been purchased
        has_orders = db.query(OrderItem).filter(OrderItem.coupon_id == coupon_id).first()
        
        if has_orders:
            # Soft-delete: deactivate instead of removing (preserves order history)
            db_coupon.is_active = False
            db.commit()
        else:
            # Hard-delete: no orders reference this coupon
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
