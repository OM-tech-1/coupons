from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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


# ---- My Wallet Schemas ----

class WalletSummaryResponse(BaseModel):
    """Summary counts for the user's coupon wallet"""
    total_coupons: int = 0
    active: int = 0
    used: int = 0
    expired: int = 0


class CategoryInWallet(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class WalletCouponResponse(BaseModel):
    """Individual coupon in the wallet list"""
    id: UUID  # UserCoupon id
    coupon_id: UUID
    code: str
    redeem_code: Optional[str] = None
    brand: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: Optional[CategoryInWallet] = None
    is_active: bool = True
    purchased_date: datetime  # claimed_at
    expires_date: Optional[datetime] = None  # coupon.expiration_date
    status: str  # "active", "used", "expired"

    class Config:
        from_attributes = True


class UserCouponDetailResponse(BaseModel):
    """Full detail view of a single user-owned coupon"""
    id: UUID  # UserCoupon id
    coupon_id: UUID
    code: str
    redeem_code: Optional[str] = None
    brand: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_amount: float
    price: float = 0.0
    category: Optional[CategoryInWallet] = None
    is_active: bool = True
    purchased_date: datetime
    expires_date: Optional[datetime] = None
    status: str  # "active", "expired"

    class Config:
        from_attributes = True
