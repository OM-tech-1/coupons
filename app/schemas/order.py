from pydantic import BaseModel

class OrderBase(BaseModel):
    total_amount: float

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
