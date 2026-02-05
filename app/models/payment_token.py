from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class PaymentToken(Base):
    """
    Short-lived tokens for secure cross-domain payment authentication.
    
    These tokens are generated when a payment is initiated and are used
    to securely transfer payment context to the payment UI domain.
    """
    __tablename__ = "payment_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(512), unique=True, nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    payment_intent_id = Column(String(255), nullable=False)
    
    # Security fields
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False)
    
    # Tracking
    site_origin = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentToken {self.id} - used:{self.is_used}>"

    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)"""
        return not self.is_expired() and not self.is_used
