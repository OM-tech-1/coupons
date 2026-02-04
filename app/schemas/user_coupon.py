from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserCouponBase(BaseModel):
    coupon_id: UUID


class UserCouponCreate(UserCouponBase):
    pass


class CouponInfo(BaseModel):
    """Embedded coupon info in user coupon response - includes redeem_code after purchase"""
    id: UUID
    code: str
    redeem_code: Optional[str] = None  # Revealed after purchase!
    brand: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_amount: float
    min_purchase: float
    expiration_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCouponResponse(BaseModel):
    id: UUID
    user_id: UUID
    coupon_id: UUID
    claimed_at: datetime
    coupon: CouponInfo

    class Config:
        from_attributes = True
