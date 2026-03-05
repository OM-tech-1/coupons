from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from app.models.package import Package
from app.models.package_coupon import PackageCoupon
from app.models.coupon import Coupon
from app.schemas.package import PackageCreate, PackageUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM


class PackageService:

    @staticmethod
    def create(db: Session, data: PackageCreate) -> Package:
        pkg = Package(
            name=data.name,
            slug=data.slug,
            description=data.description,
            picture_url=data.picture_url,
            brand=data.brand,
            discount=data.discount,
            avg_rating=data.avg_rating,
            total_sold=data.total_sold,
            category_id=data.category_id,
            is_active=data.is_active,
            is_featured=data.is_featured,
            is_trending=data.is_trending,
            expiration_date=data.expiration_date,
            country=data.country,
        )
        db.add(pkg)
        db.flush()

        if data.coupon_ids:
            for cid in data.coupon_ids:
                db.add(PackageCoupon(package_id=pkg.id, coupon_id=cid))
            db.query(Coupon).filter(Coupon.id.in_(data.coupon_ids)).update(
                {Coupon.is_package_coupon: True}, synchronize_session="fetch"
            )

        db.commit()
        db.refresh(pkg)
        invalidate_cache("packages:*")
        return PackageService._load_full(db, pkg.id)

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        is_trending: Optional[bool] = None,
        filter_by: Optional[str] = None,
        country: Optional[str] = None,
        brands: Optional[List[str]] = None,
    ) -> List[dict]:
        # Simplified cache key for better hit rates
        use_cache = (skip == 0 and limit <= 100)
        brands_key = ",".join(sorted(brands)) if brands else None
        cache_k = None
        
        if use_cache:
            cache_k = cache_key("packages", "list", category_id, is_active, is_featured, is_trending, filter_by, brands_key, country, limit)
            cached = get_cache(cache_k)
            if cached is not None:
                return cached

        # Optimized query with eager loading
        coupon_count = func.count(PackageCoupon.id).label("coupon_count")
        query = (
            db.query(Package, coupon_count)
            .outerjoin(PackageCoupon, PackageCoupon.package_id == Package.id)
            .group_by(Package.id)
        )

        if is_active is not None:
            query = query.filter(Package.is_active == is_active)
        if is_featured is not None:
            query = query.filter(Package.is_featured == is_featured)
        if is_trending is not None:
            query = query.filter(Package.is_trending == is_trending)
        if category_id is not None:
            query = query.filter(Package.category_id == category_id)
        if country is not None:
            query = query.filter(Package.country == country)
        if brands:
            query = query.filter(Package.brand.in_(brands))

        # Apply filter-based ordering
        if filter_by == "highest_saving":
            query = query.order_by(Package.discount.desc().nullslast(), Package.created_at.desc())
        elif filter_by == "avg_rating":
            query = query.order_by(Package.avg_rating.desc(), Package.created_at.desc())
        elif filter_by == "bundle_sold":
            query = query.order_by(Package.total_sold.desc(), Package.created_at.desc())
        else:
            # Default and "newest" both sort by created_at desc
            query = query.order_by(Package.created_at.desc())

        query = query.offset(skip).limit(limit)
        rows = query.all()

        result = []
        # Batch load categories to avoid N+1
        package_ids = [pkg.id for pkg, _ in rows]
        category_ids = [pkg.category_id for pkg, _ in rows if pkg.category_id]
        
        categories_map = {}
        if category_ids:
            from app.models.category import Category
            categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
            categories_map = {cat.id: cat for cat in categories}
        
        # Batch load package coupons
        package_coupons = db.query(PackageCoupon).filter(
            PackageCoupon.package_id.in_(package_ids)
        ).all()
        package_coupons_map = {}
        all_coupon_ids = set()
        for pc in package_coupons:
            if pc.package_id not in package_coupons_map:
                package_coupons_map[pc.package_id] = []
            package_coupons_map[pc.package_id].append(pc.coupon_id)
            all_coupon_ids.add(pc.coupon_id)
            
        coupons_map = {}
        if all_coupon_ids:
            all_coupons = db.query(Coupon.id, Coupon.pricing, Coupon.price).filter(Coupon.id.in_(all_coupon_ids)).all()
            coupons_map = {c.id: c for c in all_coupons}
        
        for pkg, count in rows:
            pkg_coupon_ids = package_coupons_map.get(pkg.id, [])
            
            pricing = {}
            for cid in pkg_coupon_ids:
                if cid in coupons_map:
                    c = coupons_map[cid]
                    if c.pricing:
                        for currency, values in c.pricing.items():
                            if currency not in pricing:
                                pricing[currency] = {"price": 0.0}
                            for k, v in values.items():
                                pricing[currency][k] = pricing[currency].get(k, 0.0) + v
                    else:
                        pricing.setdefault("DEFAULT", {"price": 0.0})
                        pricing["DEFAULT"]["price"] += (c.price or 0.0)
            
            prices = {}
            final_prices = {}
            for currency, values in pricing.items():
                base_price = values.get("price", 0.0)
                prices[currency] = base_price
                if pkg.discount:
                    final_prices[currency] = base_price * (1.0 - pkg.discount / 100.0)
                else:
                    final_prices[currency] = base_price

            result.append({
                "id": pkg.id,
                "name": pkg.name,
                "slug": pkg.slug,
                "description": pkg.description,
                "picture_url": pkg.picture_url,
                "brand": pkg.brand,
                "discount": pkg.discount,
                "avg_rating": pkg.avg_rating or 0.0,
                "total_sold": pkg.total_sold or 0,
                "category_id": pkg.category_id,
                "is_active": pkg.is_active,
                "is_featured": pkg.is_featured,
                "is_trending": getattr(pkg, 'is_trending', False),
                "expiration_date": pkg.expiration_date,
                "country": pkg.country,
                "created_at": pkg.created_at,
                "coupon_count": count,
                "pricing": prices,
                "final_prices": final_prices,
            })

        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result

    @staticmethod
    def get_by_id(db: Session, package_id: UUID) -> Optional[dict]:
        # Try cache first
        cache_k = cache_key("packages", "id", str(package_id))
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        result = PackageService._load_full(db, package_id)
        
        # Cache the result
        if result:
            set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        
        return result

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[dict]:
        # Try cache first
        cache_k = cache_key("packages", "slug", slug)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        pkg = db.query(Package).filter(Package.slug == slug).first()
        if not pkg:
            return None
        
        result = PackageService._load_full(db, pkg.id)
        
        # Cache the result
        if result:
            set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        
        return result

    @staticmethod
    def get_coupons(db: Session, package_id: UUID) -> List[Coupon]:
        assocs = db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()
        coupon_ids = [a.coupon_id for a in assocs]
        if not coupon_ids:
            return []
        return db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).all()

    @staticmethod
    def update(db: Session, package_id: UUID, data: PackageUpdate) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None

        update_data = data.model_dump(exclude_unset=True)
        coupon_ids = update_data.pop("coupon_ids", None)

        for field, value in update_data.items():
            setattr(pkg, field, value)

        if coupon_ids is not None:
            # Get old coupon IDs before removing
            old_ids = [a.coupon_id for a in db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()]
            removed_ids = [cid for cid in old_ids if cid not in coupon_ids]

            # Remove old associations
            db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).delete()
            # Add new ones
            for cid in coupon_ids:
                db.add(PackageCoupon(package_id=package_id, coupon_id=cid))
            # Mark new coupons
            db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).update(
                {Coupon.is_package_coupon: True}, synchronize_session="fetch"
            )
            # Reset flag on removed coupons not in any other package
            if removed_ids:
                PackageService._reset_orphaned_flags(db, removed_ids)

        db.commit()
        db.refresh(pkg)
        invalidate_cache("packages:*")
        invalidate_cache(f"packages:id:{package_id}")
        invalidate_cache(f"packages:slug:*")
        return PackageService._load_full(db, package_id)

    @staticmethod
    def delete(db: Session, package_id: UUID) -> bool:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return False
        
        # Check if package is referenced in orders
        from app.models.order import OrderItem
        has_orders = db.query(OrderItem).filter(OrderItem.package_id == package_id).first()
        
        if has_orders:
            # Soft delete: mark as inactive instead of hard delete
            pkg.is_active = False
            pkg.is_featured = False
            db.commit()
            invalidate_cache("packages:*")
            invalidate_cache(f"packages:id:{package_id}")
            invalidate_cache(f"packages:slug:*")
            return True
        
        # No orders, safe to hard delete
        # Get coupon IDs before deleting
        coupon_ids = [a.coupon_id for a in db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()]
        db.delete(pkg)
        db.flush()
        # Reset flag on coupons no longer in any package
        if coupon_ids:
            PackageService._reset_orphaned_flags(db, coupon_ids)
        db.commit()
        invalidate_cache("packages:*")
        invalidate_cache(f"packages:id:{package_id}")
        invalidate_cache(f"packages:slug:*")
        return True

    @staticmethod
    def add_coupons(db: Session, package_id: UUID, coupon_ids: List[UUID]) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None

        existing = {
            a.coupon_id
            for a in db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()
        }
        new_ids = [cid for cid in coupon_ids if cid not in existing]

        for cid in new_ids:
            db.add(PackageCoupon(package_id=package_id, coupon_id=cid))

        if new_ids:
            db.query(Coupon).filter(Coupon.id.in_(new_ids)).update(
                {Coupon.is_package_coupon: True}, synchronize_session="fetch"
            )

        db.commit()
        invalidate_cache("packages:*")
        invalidate_cache(f"packages:id:{package_id}")
        invalidate_cache(f"packages:slug:*")
        return PackageService._load_full(db, package_id)

    @staticmethod
    def remove_coupon(db: Session, package_id: UUID, coupon_id: UUID) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None

        deleted = (
            db.query(PackageCoupon)
            .filter(PackageCoupon.package_id == package_id, PackageCoupon.coupon_id == coupon_id)
            .delete()
        )
        if not deleted:
            return None

        # Reset flag if coupon is no longer in any package
        PackageService._reset_orphaned_flags(db, [coupon_id])

        db.commit()
        invalidate_cache("packages:*")
        invalidate_cache(f"packages:id:{package_id}")
        invalidate_cache(f"packages:slug:*")
        return PackageService._load_full(db, package_id)

    @staticmethod
    def _reset_orphaned_flags(db: Session, coupon_ids: List[UUID]):
        """Reset is_package_coupon=False for coupons not in any other package."""
        for cid in coupon_ids:
            still_in_package = db.query(PackageCoupon).filter(PackageCoupon.coupon_id == cid).first()
            if not still_in_package:
                db.query(Coupon).filter(Coupon.id == cid).update(
                    {Coupon.is_package_coupon: False}, synchronize_session="fetch"
                )

    @staticmethod
    def _compute_pricing(db: Session, coupon_ids: List[UUID]) -> dict:
        """Sum coupon prices per currency. Uses each coupon's `pricing` JSON
        and falls back to the base `price` field under a 'DEFAULT' key."""
        if not coupon_ids:
            return {}
        coupons = db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).all()
        totals: dict = {}
        for c in coupons:
            if c.pricing:
                for currency, values in c.pricing.items():
                    if currency not in totals:
                        totals[currency] = {"price": 0.0}
                    for k, v in values.items():
                        totals[currency][k] = totals[currency].get(k, 0.0) + v
            else:
                # Coupon has no multi-currency pricing
                totals.setdefault("DEFAULT", {"price": 0.0})
                totals["DEFAULT"]["price"] += 0.0
        return totals

    @staticmethod
    def _load_full(db: Session, package_id: UUID) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None

        cat = None
        if pkg.category_id:
            from app.models.category import Category
            cat_obj = db.get(Category, pkg.category_id)
            if cat_obj:
                cat = {"id": cat_obj.id, "name": cat_obj.name, "slug": cat_obj.slug}

        assocs = db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()
        coupon_ids = [a.coupon_id for a in assocs]
        coupons = []
        if coupon_ids:
            coupon_objs = db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).all()
            for c in coupon_objs:
                c_pricing = {}
                c_discounts = {}
                if c.pricing and isinstance(c.pricing, dict):
                    for currency, values in c.pricing.items():
                        c_pricing[currency] = values.get('price', 0.0)
                        c_discounts[currency] = values.get('discount_amount', 0.0)
                else:
                    c_pricing['USD'] = 0.0
                    c_discounts['USD'] = c.discount_amount or 0.0
                    
                coupons.append({
                    "id": c.id,
                    "title": c.title,
                    "brand": c.brand,
                    "discount_type": c.discount_type,
                    "discount_amount": c.discount_amount,
                    "picture_url": c.picture_url,
                    "pricing": c_pricing,
                    "discounts": c_discounts,
                    "is_active": c.is_active,
                })

        pricing_raw = PackageService._compute_pricing(db, coupon_ids)
        
        prices = {}
        final_prices = {}
        for currency, values in pricing_raw.items():
            base_price = values.get("price", 0.0)
            prices[currency] = base_price
            if pkg.discount:
                final_prices[currency] = base_price * (1.0 - pkg.discount / 100.0)
            else:
                final_prices[currency] = base_price

        return {
            "id": pkg.id,
            "name": pkg.name,
            "slug": pkg.slug,
            "description": pkg.description,
            "picture_url": pkg.picture_url,
            "brand": pkg.brand,
            "discount": pkg.discount,
            "avg_rating": pkg.avg_rating or 0.0,
            "total_sold": pkg.total_sold or 0,
            "max_saving": pkg.discount or 0.0,
            "pricing": prices,
            "final_prices": final_prices,
            "category_id": pkg.category_id,
            "is_active": pkg.is_active,
            "is_featured": pkg.is_featured,
            "is_trending": getattr(pkg, 'is_trending', False),
            "expiration_date": pkg.expiration_date,
            "country": pkg.country,
            "created_at": pkg.created_at,
            "category": cat,
            "coupons": coupons,
        }

    @staticmethod
    def _compute_total_price(pricing: dict) -> dict:
        """Flatten pricing into a simple {currency: total_price} map."""
        if not pricing:
            return {}
        return {currency: values.get("price", 0.0) for currency, values in pricing.items()}
