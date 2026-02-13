from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending", index=True)
    payment_id = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    
    # Stripe payment tracking
    payment_state = Column(String(20), default="awaiting_payment")
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    
    # External Reference
    reference_id = Column(String(255), unique=True, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False, index=True)
    quantity = Column(Float, default=1)
    price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    coupon = relationship("Coupon")
