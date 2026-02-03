from pydantic import BaseModel
from datetime import datetime

class CouponBase(BaseModel):
    code: str
    discount_amount: float
    expiration_date: datetime

class CouponCreate(CouponBase):
    pass

class Coupon(CouponBase):
    id: int

    class Config:
        orm_mode = True
