from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid
from app.database import Base


class PaymentStatus(str, Enum):
    """Payment status states"""
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentGateway(str, Enum):
    """Supported payment gateways"""
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False)
    
    # Stripe-specific fields
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_client_secret = Column(String(255), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)  # Store in smallest unit (cents)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(20), default=PaymentStatus.INITIATED.value)
    
    # Gateway info
    gateway = Column(String(50), default=PaymentGateway.STRIPE.value)
    
    # Additional metadata from gateway (renamed from 'metadata' which is reserved)
    payment_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"

    def is_completed(self) -> bool:
        """Check if payment reached a terminal state"""
        return self.status in [
            PaymentStatus.SUCCEEDED.value,
            PaymentStatus.FAILED.value,
            PaymentStatus.CANCELLED.value,
            PaymentStatus.REFUNDED.value
        ]

    def can_be_retried(self) -> bool:
        """Check if payment can be retried"""
        return self.status in [
            PaymentStatus.INITIATED.value,
            PaymentStatus.FAILED.value
        ]
