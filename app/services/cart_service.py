from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional, Tuple

from app.models.cart import CartItem
from app.models.coupon import Coupon
from app.models.package import Package
from app.models.package_coupon import PackageCoupon
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_SHORT


class CartService:

    @staticmethod
    def add_to_cart(db: Session, user_id: UUID, coupon_id: UUID, quantity: int = 1) -> Tuple[Optional[CartItem], str]:
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return None, "Coupon not found"

        if not coupon.is_active:
            return None, "Coupon is not active"

        existing = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.coupon_id == coupon_id
        ).first()

        if existing:
            existing.quantity += quantity
            try:
                db.commit()
                db.refresh(existing)
                # Invalidate cart cache
                invalidate_cache(f"cart:{user_id}:*")
                return existing, "Quantity updated"
            except StaleDataError:
                db.rollback()
                existing = None

        cart_item = CartItem(
            user_id=user_id,
            coupon_id=coupon_id,
            quantity=quantity
        )
        db.add(cart_item)
        try:
            db.commit()
            db.refresh(cart_item)
            # Invalidate cart cache
            invalidate_cache(f"cart:{user_id}:*")
            return cart_item, "Added to cart"
        except IntegrityError:
            db.rollback()
            existing = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.coupon_id == coupon_id
            ).first()
            if existing:
                existing.quantity += quantity
                db.commit()
                db.refresh(existing)
                invalidate_cache(f"cart:{user_id}:*")
                return existing, "Quantity updated"
            return None, "Failed to add to cart"

    @staticmethod
    def add_package_to_cart(db: Session, user_id: UUID, package_id: UUID, quantity: int = 1) -> Tuple[Optional[CartItem], str]:
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            return None, "Package not found"

        if not package.is_active:
            return None, "Package is not active"

        existing = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.package_id == package_id
        ).first()

        if existing:
            existing.quantity += quantity
            try:
                db.commit()
                db.refresh(existing)
                # Invalidate cart cache
                invalidate_cache(f"cart:{user_id}:*")
                return existing, "Quantity updated"
            except StaleDataError:
                db.rollback()
                existing = None

        cart_item = CartItem(
            user_id=user_id,
            package_id=package_id,
            quantity=quantity
        )
        db.add(cart_item)
        try:
            db.commit()
            db.refresh(cart_item)
            # Invalidate cart cache
            invalidate_cache(f"cart:{user_id}:*")
            return cart_item, "Added to cart"
        except IntegrityError:
            db.rollback()
            existing = db.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.package_id == package_id
            ).first()
            if existing:
                existing.quantity += quantity
                db.commit()
                db.refresh(existing)
                invalidate_cache(f"cart:{user_id}:*")
                return existing, "Quantity updated"
            return None, "Failed to add to cart"

    @staticmethod
    def get_cart(db: Session, user_id: UUID) -> List[CartItem]:
        # Try cache first
        cache_k = cache_key("cart", str(user_id), "items")
        cached = get_cache(cache_k)
        
        if cached is not None:
            # Reconstruct CartItem objects from cache
            # Note: We still need to query for relationships, but this reduces load
            pass  # For now, skip complex reconstruction and query DB
        
        # Query database with eager loading
        items = db.query(CartItem).options(
            joinedload(CartItem.coupon),
            joinedload(CartItem.package).joinedload(Package.coupon_associations).joinedload(PackageCoupon.coupon),
        ).filter(CartItem.user_id == user_id).all()
        
        # Cache the result (short TTL since cart changes frequently)
        # We cache a simplified version to avoid serialization issues
        try:
            cache_data = [
                {
                    "id": str(item.id),
                    "coupon_id": str(item.coupon_id) if item.coupon_id else None,
                    "package_id": str(item.package_id) if item.package_id else None,
                    "quantity": item.quantity,
                }
                for item in items
            ]
            set_cache(cache_k, cache_data, CACHE_TTL_SHORT)
        except Exception:
            pass  # Don't fail if caching fails
        
        return items

    @staticmethod
    def get_cart_total(db: Session, user_id: UUID) -> float:
        items = CartService.get_cart(db, user_id)
        total = 0.0
        for item in items:
            if item.coupon:
                total += (item.coupon.price or 0) * item.quantity
            elif item.package:
                base_sum = sum(c.coupon.price for c in item.package.coupon_associations if c.coupon and c.coupon.price)
                discount = item.package.discount or 0.0
                pkg_price = base_sum * (1.0 - discount / 100.0)
                total += pkg_price * item.quantity
        return total

    @staticmethod
    def remove_from_cart(db: Session, user_id: UUID, item_id: UUID) -> bool:
        """
        Remove a cart item by its ID.
        The item_id is the CartItem's primary key (id field).
        This works for both coupons and packages.
        """
        item = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.id == item_id
        ).first()
        if item:
            db.delete(item)
            db.commit()
            # Invalidate cart cache
            invalidate_cache(f"cart:{user_id}:*")
            return True
        return False

    @staticmethod
    def clear_cart(db: Session, user_id: UUID) -> int:
        deleted = db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        db.commit()
        # Invalidate cart cache
        invalidate_cache(f"cart:{user_id}:*")
        return deleted
