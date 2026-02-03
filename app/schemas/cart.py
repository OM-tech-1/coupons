from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class CartItemBase(BaseModel):
    coupon_id: UUID
    quantity: int = 1


class CartItemCreate(CartItemBase):
    pass


class CouponInCart(BaseModel):
    id: UUID
    code: str
    title: str
    price: float
    discount_amount: float
    
    class Config:
        from_attributes = True


class CartItemResponse(BaseModel):
    id: UUID
    coupon_id: UUID
    quantity: int
    added_at: datetime
    coupon: CouponInCart
    
    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: float
