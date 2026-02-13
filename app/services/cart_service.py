from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional, Tuple

from app.models.cart import CartItem
from app.models.coupon import Coupon


class CartService:
    
    @staticmethod
    def add_to_cart(db: Session, user_id: UUID, coupon_id: UUID, quantity: int = 1) -> Tuple[Optional[CartItem], str]:
        """Add a coupon to user's cart"""
        # Check if coupon exists
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return None, "Coupon not found"
        
        if not coupon.is_active:
            return None, "Coupon is not active"
        
        # Check if already in cart
        existing = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.coupon_id == coupon_id
        ).first()
        
        if existing:
            existing.quantity += quantity
            db.commit()
            db.refresh(existing)
            return existing, "Quantity updated"
        
        # Add new item
        cart_item = CartItem(
            user_id=user_id,
            coupon_id=coupon_id,
            quantity=quantity
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item, "Added to cart"

    @staticmethod
    def get_cart(db: Session, user_id: UUID) -> List[CartItem]:
        """Get all items in user's cart (with coupon details eagerly loaded)"""
        return db.query(CartItem).options(
            joinedload(CartItem.coupon)
        ).filter(CartItem.user_id == user_id).all()

    @staticmethod
    def get_cart_total(db: Session, user_id: UUID) -> float:
        """Calculate cart total"""
        items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
        total = 0.0
        for item in items:
            if item.coupon:
                total += (item.coupon.price or 0) * item.quantity
        return total

    @staticmethod
    def remove_from_cart(db: Session, user_id: UUID, coupon_id: UUID) -> bool:
        """Remove a coupon from cart"""
        item = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.coupon_id == coupon_id
        ).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return False

    @staticmethod
    def clear_cart(db: Session, user_id: UUID) -> int:
        """Clear all items from cart"""
        deleted = db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        db.commit()
        return deleted
