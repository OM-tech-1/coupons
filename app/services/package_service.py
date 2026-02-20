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
            category_id=data.category_id,
            is_active=data.is_active,
            is_featured=data.is_featured,
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
    ) -> List[dict]:
        cache_k = cache_key("packages", "list", skip, limit, category_id, is_active, is_featured)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached

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
        if category_id is not None:
            query = query.filter(Package.category_id == category_id)

        query = query.order_by(Package.created_at.desc()).offset(skip).limit(limit)
        rows = query.all()

        result = []
        for pkg, count in rows:
            cat = None
            if pkg.category_id:
                from app.models.category import Category
                cat_obj = db.query(Category).get(pkg.category_id)
                if cat_obj:
                    cat = {"id": cat_obj.id, "name": cat_obj.name, "slug": cat_obj.slug}
            # Compute pricing from associated coupons
            pkg_coupon_ids = [a.coupon_id for a in db.query(PackageCoupon).filter(PackageCoupon.package_id == pkg.id).all()]
            pricing = PackageService._compute_pricing(db, pkg_coupon_ids)
            result.append({
                "id": pkg.id,
                "name": pkg.name,
                "slug": pkg.slug,
                "description": pkg.description,
                "picture_url": pkg.picture_url,
                "pricing": pricing,
                "category_id": pkg.category_id,
                "is_active": pkg.is_active,
                "is_featured": pkg.is_featured,
                "created_at": pkg.created_at,
                "category": cat,
                "coupon_count": count,
            })

        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result

    @staticmethod
    def get_by_id(db: Session, package_id: UUID) -> Optional[dict]:
        return PackageService._load_full(db, package_id)

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.slug == slug).first()
        if not pkg:
            return None
        return PackageService._load_full(db, pkg.id)

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
            # Remove old associations
            db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).delete()
            # Add new ones
            for cid in coupon_ids:
                db.add(PackageCoupon(package_id=package_id, coupon_id=cid))
            # Mark new coupons
            db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).update(
                {Coupon.is_package_coupon: True}, synchronize_session="fetch"
            )

        db.commit()
        db.refresh(pkg)
        invalidate_cache("packages:*")
        return PackageService._load_full(db, package_id)

    @staticmethod
    def delete(db: Session, package_id: UUID) -> bool:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return False
        db.delete(pkg)
        db.commit()
        invalidate_cache("packages:*")
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

        db.commit()
        invalidate_cache("packages:*")
        return PackageService._load_full(db, package_id)

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
                # Coupon has no multi-currency pricing, use base price
                totals.setdefault("DEFAULT", {"price": 0.0})
                totals["DEFAULT"]["price"] += (c.price or 0.0)
        return totals

    @staticmethod
    def _load_full(db: Session, package_id: UUID) -> Optional[dict]:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None

        cat = None
        if pkg.category_id:
            from app.models.category import Category
            cat_obj = db.query(Category).get(pkg.category_id)
            if cat_obj:
                cat = {"id": cat_obj.id, "name": cat_obj.name, "slug": cat_obj.slug}

        assocs = db.query(PackageCoupon).filter(PackageCoupon.package_id == package_id).all()
        coupon_ids = [a.coupon_id for a in assocs]
        coupons = []
        if coupon_ids:
            coupon_objs = db.query(Coupon).filter(Coupon.id.in_(coupon_ids)).all()
            coupons = [
                {
                    "id": c.id,
                    "title": c.title,
                    "brand": c.brand,
                    "discount_type": c.discount_type,
                    "discount_amount": c.discount_amount,
                    "picture_url": c.picture_url,
                }
                for c in coupon_objs
            ]

        pricing = PackageService._compute_pricing(db, coupon_ids)

        return {
            "id": pkg.id,
            "name": pkg.name,
            "slug": pkg.slug,
            "description": pkg.description,
            "picture_url": pkg.picture_url,
            "pricing": pricing,
            "category_id": pkg.category_id,
            "is_active": pkg.is_active,
            "is_featured": pkg.is_featured,
            "created_at": pkg.created_at,
            "category": cat,
            "coupons": coupons,
        }
