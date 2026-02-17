from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    redeem_code = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), default="percentage")
    discount_amount = Column(Float, nullable=False)
    price = Column(Float, default=0.0)
    min_purchase = Column(Float, default=0.0)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expiration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    picture_url = Column(String(500), nullable=True)
    stock = Column(Integer, nullable=True, default=None)
    pricing = Column(JSON, nullable=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    availability_type = Column(String(20), default="online", index=True)
    
    # Relationships
    category = relationship("Category", back_populates="coupons")
    country_associations = relationship("CouponCountry", back_populates="coupon", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_coupons_active_featured', 'is_active', 'is_featured'),
        Index('ix_coupons_active_created', 'is_active', 'created_at'),
    )

