from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import Token, ChangePasswordRequest
from app.schemas.unified_auth import UnifiedRegisterRequest, UnifiedLoginRequest
from app.schemas.user import UserResponse
from app.services.auth_service import register_user, authenticate_user, change_password
from app.utils.jwt import create_access_token
from app.utils.currency import get_currency_from_phone_code
from app.utils.security import get_current_active_user
from app.models.user import User

from app.middleware.rate_limit import limiter
import logging

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=UserResponse)
@limiter.limit("10/minute")
def register(request: Request, user_data: UnifiedRegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or phone number already exists"
        )
    return user

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, payload: UnifiedLoginRequest, db: Session = Depends(get_db)):
    logger = logging.getLogger(__name__)
    
    # Log attempt based on available identifier
    identifier_log = payload.email if payload.email else f"{payload.country_code} {payload.number}"
    logger.info(f"Login attempt for: {identifier_log}")
    
    user = authenticate_user(db, payload)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Calculate currency once and store in token
    # Defaulting to USD if falling back to an email-only user without a real phone number
    currency_code = get_currency_from_phone_code(user.phone_number) if user.phone_number and getattr(user, 'phone_number').startswith('+') else "USD"
    access_token = create_access_token(
        data={"sub": str(user.id)},
        currency=currency_code
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/change-password")
@limiter.limit("5/minute")
def change_password_endpoint(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password.
    
    Requires valid Bearer token. Rate limited to 5 requests per minute.
    Returns 403 if current_password is incorrect.
    """
    success = change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current password is incorrect",
        )
    return {"success": True, "message": "Password updated successfully"}

from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import generate_reset_token, verify_reset_token_and_update_password
from app.utils.email import send_reset_email
from fastapi import BackgroundTasks

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal if user exists or not for security
        return {"success": True, "message": "If that email is registered, a password reset link has been sent."}
    
    token = generate_reset_token(db, user)
    # Send email in background to not block the request
    background_tasks.add_task(send_reset_email, payload.email, token)
    
    return {"success": True, "message": "If that email is registered, a password reset link has been sent."}

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    success = verify_reset_token_and_update_password(db, payload.token, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token, or password has already been changed."
        )
        
    return {"success": True, "message": "Password successfully reset."}