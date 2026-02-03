from pydantic import BaseModel

class PaymentBase(BaseModel):
    amount: float
    status: str

class PaymentCreate(PaymentBase):
    order_id: int

class Payment(PaymentBase):
    id: int

    class Config:
        orm_mode = True
