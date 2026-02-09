from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Display code/SKU
    redeem_code = Column(String(100), nullable=True)  # Actual code revealed after purchase
    brand = Column(String(100), nullable=True)  # Brand/company name (McDonald's, Amazon, etc.)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), default="percentage")  # "percentage" or "fixed"
    discount_amount = Column(Float, nullable=False)
    price = Column(Float, default=0.0)  # Price to purchase this coupon (0 = free)
    min_purchase = Column(Float, default=0.0)
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expiration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New fields for stock and featured
    stock = Column(Integer, nullable=True, default=None)  # Available stock (None = unlimited)
    is_featured = Column(Boolean, default=False, index=True)  # Featured on homepage
    
    # Fields for categories and geography
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    availability_type = Column(String(20), default="online", index=True)  # 'online', 'local', or 'both'
    
    # Relationships
    category = relationship("Category", back_populates="coupons")
    country_associations = relationship("CouponCountry", back_populates="coupon", cascade="all, delete-orphan")

