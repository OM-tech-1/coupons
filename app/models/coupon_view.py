from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class CouponView(Base):
    __tablename__ = "coupon_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String(100), nullable=True, index=True)  # For tracking anonymous users
    
    # Relationships
    coupon = relationship("Coupon")
    user = relationship("User")
