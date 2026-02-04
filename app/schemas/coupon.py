from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class CouponBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    redeem_code: Optional[str] = Field(default=None, max_length=100, description="Actual code revealed after purchase")
    brand: Optional[str] = Field(default=None, max_length=100, description="Brand/company name")
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    discount_type: str = Field(default="percentage", pattern="^(percentage|fixed)$")
    discount_amount: float = Field(..., gt=0)
    min_purchase: float = Field(default=0.0, ge=0)
    max_uses: Optional[int] = Field(default=None, ge=1)
    expiration_date: Optional[datetime] = None


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=3, max_length=50)
    redeem_code: Optional[str] = Field(default=None, max_length=100)
    brand: Optional[str] = Field(default=None, max_length=100)
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = None
    discount_type: Optional[str] = Field(default=None, pattern="^(percentage|fixed)$")
    discount_amount: Optional[float] = Field(default=None, gt=0)
    min_purchase: Optional[float] = Field(default=None, ge=0)
    max_uses: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None
    expiration_date: Optional[datetime] = None


class CouponResponse(CouponBase):
    id: UUID
    price: float = 0.0
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CouponValidateRequest(BaseModel):
    """Request schema for coupon validation"""
    code: str = Field(..., min_length=1, max_length=50, description="Coupon code to validate")
    purchase_amount: Optional[float] = Field(default=None, ge=0, description="Purchase amount to calculate discount")


class CouponValidateResponse(BaseModel):
    """Response schema for coupon validation"""
    valid: bool
    code: str
    message: str
    discount_type: Optional[str] = None
    discount_amount: Optional[float] = None
    min_purchase: Optional[float] = None
    calculated_discount: Optional[float] = None
    final_amount: Optional[float] = None
