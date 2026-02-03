from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class OrderItemResponse(BaseModel):
    id: UUID
    coupon_id: UUID
    quantity: float
    price: float
    
    class Config:
        from_attributes = True


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
    payment_method: str = "mock"  # mock, razorpay, stripe


class PaymentVerifyRequest(BaseModel):
    order_id: UUID
    payment_id: str
    signature: Optional[str] = None  # For Razorpay signature verification
