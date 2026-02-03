from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate


class CouponService:
    
    @staticmethod
    def create(db: Session, coupon_data: CouponCreate) -> Coupon:
        """Create a new coupon"""
        db_coupon = Coupon(
            code=coupon_data.code.upper(),
            title=coupon_data.title,
            description=coupon_data.description,
            discount_type=coupon_data.discount_type,
            discount_amount=coupon_data.discount_amount,
            min_purchase=coupon_data.min_purchase,
            max_uses=coupon_data.max_uses,
            expiration_date=coupon_data.expiration_date,
        )
        db.add(db_coupon)
        db.commit()
        db.refresh(db_coupon)
        return db_coupon

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Coupon]:
        """Get all coupons with optional filtering"""
        query = db.query(Coupon)
        if active_only:
            query = query.filter(Coupon.is_active == True)
        return query.offset(skip).limit(limit).all()

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
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return None
        
        update_data = coupon_data.model_dump(exclude_unset=True)
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper()
        
        for field, value in update_data.items():
            setattr(db_coupon, field, value)
        
        db.commit()
        db.refresh(db_coupon)
        return db_coupon

    @staticmethod
    def delete(db: Session, coupon_id: UUID) -> bool:
        """Delete a coupon"""
        db_coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not db_coupon:
            return False
        
        db.delete(db_coupon)
        db.commit()
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
