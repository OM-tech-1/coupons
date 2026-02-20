from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(220), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    picture_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)

    category = relationship("Category")
    coupon_associations = relationship("PackageCoupon", back_populates="package", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_packages_active_featured', 'is_active', 'is_featured'),
    )
