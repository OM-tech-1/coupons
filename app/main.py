from fastapi import FastAPI
from app.api import auth, coupons, users
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coupon E-commerce API")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
app.include_router(users.router, prefix="/user", tags=["User"])


@app.get("/")
def health_check():
    return {"status": "OK"}