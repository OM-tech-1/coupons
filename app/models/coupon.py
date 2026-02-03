from sqlalchemy import Column, Integer, String, Float, DateTime
from ..database import Base

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    discount_amount = Column(Float)
    expiration_date = Column(DateTime)
