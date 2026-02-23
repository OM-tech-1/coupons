from pydantic import BaseModel, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID


class CartItemCreate(BaseModel):
    package_id: Optional[UUID] = None
    coupon_id: Optional[UUID] = None
    quantity: int = 1

    @model_validator(mode='after')
    def check_ids(self):
        if not self.package_id and not self.coupon_id:
            raise ValueError('Either package_id or coupon_id must be provided')
        if self.package_id and self.coupon_id:
            raise ValueError('Provide either package_id or coupon_id, not both')
        if self.quantity < 1:
            raise ValueError('Quantity must be at least 1')
        return self


class CouponInCart(BaseModel):
    id: UUID
    code: str
    title: str
    price: float
    discount_amount: float
    currency: str = "USD"
    currency_symbol: str = "$"

    class Config:
        from_attributes = True


class PackageInCart(BaseModel):
    id: UUID
    name: str
    slug: str
    discount: Optional[float] = None
    picture_url: Optional[str] = None
    price: Optional[float] = None
    pricing: Optional[Dict[str, Dict[str, float]]] = None
    total_price: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


class CartItemResponse(BaseModel):
    id: UUID
    coupon_id: Optional[UUID] = None
    package_id: Optional[UUID] = None
    quantity: int
    added_at: datetime
    coupon: Optional[CouponInCart] = None
    package: Optional[PackageInCart] = None

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: float
