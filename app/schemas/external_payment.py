
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from decimal import Decimal
from uuid import UUID

class ExternalPaymentRequest(BaseModel):
    phone_number: str = Field(..., description="User's phone number with country code")
    amount: Decimal = Field(..., gt=0, description="Amount to charge in standard currency unit (e.g., 100.50)")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code (e.g., USD, AED)")
    first_name: Optional[str] = Field(None, description="User's first name")
    second_name: Optional[str] = Field(None, description="User's second/last name")
    reference_id: Optional[str] = Field(None, description="External reference ID for reconciliation")
    return_url: Optional[HttpUrl] = Field(None, description="URL to redirect user after payment completion")
    webhook_url: Optional[HttpUrl] = Field(None, description="URL to receive server-to-server payment notifications")

class ExternalPaymentResponse(BaseModel):
    payment_url: str
    order_id: UUID
    user_status: str  # "existing" or "created"
    amount: Decimal
    currency: str
