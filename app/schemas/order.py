from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class CategoryInOrder(BaseModel):
    """Simplified category info nested in order coupon details"""
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class CouponInOrder(BaseModel):
    """Coupon details embedded in order item responses"""
    code: str
    redeem_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: Optional[str] = None
    is_active: bool = True
    expiration_date: Optional[datetime] = None
    category: Optional[CategoryInOrder] = None

    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    id: UUID
    coupon_id: UUID
    quantity: float
    price: float
    coupon: Optional[CouponInOrder] = None
    
    # Flattened fields for convenience
    coupon_title: Optional[str] = None
    coupon_description: Optional[str] = None
    coupon_type: Optional[str] = None
    
    class Config:
        from_attributes = True

    @model_validator(mode='after')
    def flatten_coupon_details(self) -> 'OrderItemResponse':
        if self.coupon:
            self.coupon_title = self.coupon.title
            self.coupon_description = self.coupon.description
            self.coupon_type = self.coupon.discount_type
        return self


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: float
    status: str
    payment_id: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    payment_method: str = "stripe"  # mock, razorpay, stripe


class PaymentVerifyRequest(BaseModel):
    order_id: UUID
    payment_id: str
    signature: Optional[str] = None  # For Razorpay signature verification
