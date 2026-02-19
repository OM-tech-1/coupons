from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import register_user, authenticate_user
from app.utils.jwt import create_access_token
from app.utils.currency import get_currency_from_phone_code

from app.middleware.rate_limit import limiter
import logging

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=UserResponse)
@limiter.limit("10/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt for phone: {payload.phone_number} (from {payload.country_code} {payload.number})")
    
    user = authenticate_user(db, payload.phone_number, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Calculate currency once and store in token
    currency_code = get_currency_from_phone_code(user.phone_number)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        currency=currency_code
    )
    return {"access_token": access_token, "token_type": "bearer"}