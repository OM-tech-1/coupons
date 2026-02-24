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


class PackageInOrder(BaseModel):
    """Package details embedded in order item responses"""
    id: UUID
    name: str
    slug: str
    picture_url: Optional[str] = None
    brand: Optional[str] = None
    discount: Optional[float] = None
    
    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    id: UUID
    coupon_id: Optional[UUID] = None
    package_id: Optional[UUID] = None
    quantity: float
    price: float
    coupon: Optional[CouponInOrder] = None
    package: Optional[PackageInOrder] = None
    
    # Flattened fields for convenience
    coupon_title: Optional[str] = None
    coupon_description: Optional[str] = None
    coupon_type: Optional[str] = None
    
    package_name: Optional[str] = None
    package_brand: Optional[str] = None
    
    class Config:
        from_attributes = True

    @model_validator(mode='after')
    def flatten_coupon_details(self) -> 'OrderItemResponse':
        if self.coupon:
            self.coupon_title = self.coupon.title
            self.coupon_description = self.coupon.description
            self.coupon_type = self.coupon.discount_type
        if self.package:
            self.package_name = self.package.name
            self.package_brand = self.package.brand
        return self


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: float
    status: str
    payment_id: Optional[str] = None
    payment_method: Optional[str] = None
    created_at: datetime
    currency: str = "USD"
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    payment_method: str = "stripe"  # mock, razorpay, stripe


class PaymentVerifyRequest(BaseModel):
    order_id: UUID
    payment_id: str
    signature: Optional[str] = None  # For Razorpay signature verification
