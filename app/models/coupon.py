from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), default="percentage")  # "percentage" or "fixed"
    discount_amount = Column(Float, nullable=False)
    min_purchase = Column(Float, default=0.0)
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expiration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
