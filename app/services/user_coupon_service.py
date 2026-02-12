from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

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

    # ---- Wallet Methods ----

    @staticmethod
    def _coupon_status(user_coupon: UserCoupon) -> str:
        """Determine the status of a user coupon: used, expired, or active"""
        # Priority: used > expired > active
        if user_coupon.used_at is not None:
            return "used"
        
        coupon = user_coupon.coupon
        now = datetime.now(timezone.utc)
        if not coupon.is_active:
            return "expired"
        if coupon.expiration_date:
            exp = coupon.expiration_date
            # Make it timezone-aware if it isn't
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                return "expired"
        return "active"

    @staticmethod
    def get_wallet_summary(db: Session, user_id: UUID) -> dict:
        """Get wallet summary counts: total, active, used, expired"""
        user_coupons = db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id
        ).options(
            joinedload(UserCoupon.coupon)
        ).all()

        total = len(user_coupons)
        active = 0
        used = 0
        expired = 0

        for uc in user_coupons:
            if uc.coupon:
                status = UserCouponService._coupon_status(uc)
                if status == "active":
                    active += 1
                elif status == "used":
                    used += 1
                else:
                    expired += 1

        return {
            "total_coupons": total,
            "active": active,
            "used": used,
            "expired": expired,
        }

    @staticmethod
    def get_wallet_coupons(db: Session, user_id: UUID) -> List[dict]:
        """Get all wallet coupons with rich details"""
        user_coupons = db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id
        ).options(
            joinedload(UserCoupon.coupon).joinedload(Coupon.category)
        ).order_by(UserCoupon.claimed_at.desc()).all()

        results = []
        for uc in user_coupons:
            coupon = uc.coupon
            if not coupon:
                continue

            category_data = None
            if coupon.category:
                category_data = {"id": coupon.category.id, "name": coupon.category.name}

            results.append({
                "id": uc.id,
                "coupon_id": coupon.id,
                "code": coupon.code,
                "redeem_code": coupon.redeem_code,
                "brand": coupon.brand,
                "title": coupon.title,
                "description": coupon.description,
                "category": category_data,
                "is_active": coupon.is_active,
                "purchased_date": uc.claimed_at,
                "expires_date": coupon.expiration_date,
                "status": UserCouponService._coupon_status(uc),
            })

        return results

    @staticmethod
    def get_user_coupon_detail(db: Session, user_id: UUID, coupon_id: UUID) -> Optional[dict]:
        """Get detailed view of a single user-owned coupon"""
        uc = db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id,
            UserCoupon.coupon_id == coupon_id
        ).options(
            joinedload(UserCoupon.coupon).joinedload(Coupon.category)
        ).first()

        if not uc or not uc.coupon:
            return None

        coupon = uc.coupon
        category_data = None
        if coupon.category:
            category_data = {"id": coupon.category.id, "name": coupon.category.name}

        return {
            "id": uc.id,
            "coupon_id": coupon.id,
            "code": coupon.code,
            "redeem_code": coupon.redeem_code,
            "brand": coupon.brand,
            "title": coupon.title,
            "description": coupon.description,
            "discount_type": coupon.discount_type,
            "discount_amount": coupon.discount_amount,
            "price": coupon.price,
            "category": category_data,
            "is_active": coupon.is_active,
            "purchased_date": uc.claimed_at,
            "expires_date": coupon.expiration_date,
            "status": UserCouponService._coupon_status(uc),
        }

    @staticmethod
    def mark_coupon_as_used(db: Session, user_id: UUID, coupon_id: UUID) -> Optional[dict]:
        """Mark a user's coupon as used/redeemed"""
        uc = db.query(UserCoupon).filter(
            UserCoupon.user_id == user_id,
            UserCoupon.coupon_id == coupon_id
        ).options(
            joinedload(UserCoupon.coupon).joinedload(Coupon.category)
        ).first()

        if not uc:
            return None

        # Mark as used with current timestamp
        uc.used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(uc)

        # Return updated coupon details
        return UserCouponService.get_user_coupon_detail(db, user_id, coupon_id)
