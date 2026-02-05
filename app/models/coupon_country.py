from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CouponCountry(Base):
    """Association table for many-to-many relationship between coupons and countries"""
    __tablename__ = "coupon_countries"

    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), primary_key=True)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    coupon = relationship("Coupon", back_populates="country_associations")
    country = relationship("Country", back_populates="coupon_associations")
    
    # Ensure unique coupon-country pairs
    __table_args__ = (
        UniqueConstraint('coupon_id', 'country_id', name='uq_coupon_country'),
    )
