from fastapi import FastAPI
from app.api import auth
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coupon E-commerce API")

app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"status": "OK"}