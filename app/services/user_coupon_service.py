from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.models.user_coupon import UserCoupon
from app.models.coupon import Coupon
from app.services.coupon_service import CouponService


class UserCouponService:
    
    @staticmethod
    def claim_coupon(db: Session, user_id: UUID, coupon_id: UUID) -> tuple[Optional[UserCoupon], str]:
        """Claim a coupon for a user"""
        # Check if coupon exists
        coupon = CouponService.get_by_id(db, coupon_id)
        if not coupon:
            return None, "Coupon not found"
        
        # Check if coupon is valid
        is_valid, message = CouponService.is_valid(coupon)
        if not is_valid:
            return None, message
        
        # Check if user already claimed this coupon
        existing = db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id,
            UserCoupon.coupon_id == coupon_id
        ).first()
        if existing:
            return None, "You have already claimed this coupon"
        
        # Create the claim
        user_coupon = UserCoupon(
            user_id=user_id,
            coupon_id=coupon_id
        )
        db.add(user_coupon)
        
        # Increment usage count
        coupon.current_uses += 1
        
        db.commit()
        db.refresh(user_coupon)
        return user_coupon, "Coupon claimed successfully"

    @staticmethod
    def get_user_coupons(db: Session, user_id: UUID) -> List[UserCoupon]:
        """Get all coupons claimed by a user"""
        return db.query(UserCoupon).filter(UserCoupon.user_id == user_id).all()

    @staticmethod
    def has_claimed(db: Session, user_id: UUID, coupon_id: UUID) -> bool:
        """Check if user has already claimed a coupon"""
        return db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id,
            UserCoupon.coupon_id == coupon_id
        ).first() is not None
