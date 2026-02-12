from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)  # When the coupon was redeemed/used

    # Relationships
    coupon = relationship("Coupon", backref="user_coupons")
