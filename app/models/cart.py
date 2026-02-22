from sqlalchemy import Column, ForeignKey, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=True, index=True)
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=True, index=True)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    coupon = relationship("Coupon")
    package = relationship("Package")

    __table_args__ = (
        UniqueConstraint('user_id', 'coupon_id', name='uq_cart_user_coupon'),
    )
