"""
Stripe Payment Schemas

Request and response models for Stripe payment endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class PaymentInitRequest(BaseModel):
    """Request to initialize a payment"""
    order_id: UUID = Field(..., description="UUID of the order to pay for")
    amount: int = Field(..., gt=0, description="Amount in smallest currency unit (cents)")
    currency: str = Field(default="USD", max_length=3, description="3-letter currency code")
    metadata: Optional[dict] = Field(default=None, description="Optional metadata")
    return_url: Optional[str] = Field(default=None, description="URL to return after payment")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "order_id": "550e8400-e29b-41d4-a716-446655440000",
            "amount": 1999,
            "currency": "USD",
        }
    })


class PaymentInitResponse(BaseModel):
    """Response after payment initialization"""
    redirect_url: str = Field(..., description="URL to redirect user for payment")
    token: str = Field(..., description="Short-lived payment token")
    expires_at: datetime = Field(..., description="Token expiration time")
    order_id: UUID = Field(..., description="Order ID")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID")


class TokenValidateRequest(BaseModel):
    """Request to validate a payment token"""
    token: str = Field(..., description="Payment token to validate")


class TokenValidateResponse(BaseModel):
    """Response after token validation"""
    client_secret: str = Field(..., description="Stripe client secret for Elements")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(..., description="Currency code")
    order_id: str = Field(..., description="Order ID")
    publishable_key: str = Field(..., description="Stripe publishable key")
    return_url: Optional[str] = Field(None, description="URL to return to after payment")


class PaymentStatusRequest(BaseModel):
    """Request to check payment status"""
    order_id: UUID = Field(..., description="Order ID to check")


class PaymentStatusResponse(BaseModel):
    """Response with payment status"""
    order_id: UUID = Field(..., description="Order ID")
    status: str = Field(..., description="Payment status")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(..., description="Currency code")
    paid_at: Optional[datetime] = Field(None, description="Payment completion time")
    gateway: str = Field(default="stripe", description="Payment gateway used")


class PaymentErrorResponse(BaseModel):
    """Error response for payment operations"""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")
