from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class PackageCoupon(Base):
    __tablename__ = "package_coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)

    package = relationship("Package", back_populates="coupon_associations")
    coupon = relationship("Coupon")

    __table_args__ = (
        UniqueConstraint("package_id", "coupon_id", name="uq_package_coupon"),
    )
