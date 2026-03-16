from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.schemas.unified_auth import UnifiedRegisterRequest, UnifiedLoginRequest
from app.utils.security import get_password_hash, verify_password, invalidate_user_cache
import random
from datetime import datetime, timedelta

def register_user(db: Session, user_data: UnifiedRegisterRequest):
    # Check if user already exists with either email or phone_number
    query = db.query(User)
    filters = []
    
    if user_data.phone_number:
        filters.append(User.phone_number == user_data.phone_number)
    if user_data.email:
        filters.append(User.email == user_data.email)
        
    if filters:
        existing_user = query.filter(or_(*filters)).first()
        if existing_user:
            return None # Indicate conflict/exists
            
    hashed_password = get_password_hash(user_data.password)
    
    # Store phone_number fallback to email if no phone is provided (schema currently handles this but db req. phone as string)
    fallback_phone = user_data.phone_number if user_data.phone_number else f"email:{user_data.email}"
    
    new_user = User(
        phone_number=fallback_phone, 
        email=user_data.email,
        full_name=user_data.full_name,
        second_name=user_data.second_name,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, login_data: UnifiedLoginRequest):
    query = db.query(User)
    filters = []
    
    # Let user auth via phone or email based on what they provided
    if login_data.phone_number:
        filters.append(User.phone_number == login_data.phone_number)
    if login_data.email:
        filters.append(User.email == login_data.email)
        
    user = query.filter(or_(*filters)).first() if filters else None
    
    if not user:
        return None
    if not verify_password(login_data.password, user.hashed_password):
        return None
    return user

def change_password(db: Session, user, current_password: str, new_password: str) -> bool:
    """Verify current password and update to new password.
    Returns True on success, False if current_password is incorrect.
    """
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    # Invalidate cached auth entry so next request re-fetches from DB
    invalidate_user_cache(str(user.id))
    return True

from jose import jwt, JWTError
from app.config import JWT_SECRET, JWT_ALGORITHM, FRONTEND_RESET_URL

def generate_reset_token(db: Session, user: User) -> str:
    """Generate a JWT containing the user ID and a salt derived from their current hashed password."""
    # Salt using the last 10 characters of the current hashed password
    salt = user.hashed_password[-10:] if user.hashed_password else "nosalt"
    
    payload = {
        "sub": str(user.id),
        "type": "password_reset",
        "salt": salt,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_reset_token_and_update_password(db: Session, token: str, new_password: str) -> bool:
    """Verify the reset token's validity, check the salt, and update the password."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "password_reset":
            return False
            
        user_id = payload.get("sub")
        token_salt = payload.get("salt")
        
        if not user_id or not token_salt:
            return False
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
            
        # Verify the salt hasn't changed (which implies the password hasn't changed since token issuance)
        current_salt = user.hashed_password[-10:] if user.hashed_password else "nosalt"
        if current_salt != token_salt:
            return False
            
        # Valid token, update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        invalidate_user_cache(str(user.id))
        return True
        
    except JWTError:
        return False