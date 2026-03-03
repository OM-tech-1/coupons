from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash, verify_password, invalidate_user_cache

def register_user(db: Session, user_data: UserCreate):
    # Check if phone number already exists
    existing_user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
    if existing_user:
        return None
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        phone_number=user_data.phone_number,
        full_name=user_data.full_name,
        second_name=user_data.second_name,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, phone_number: str, password: str):
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
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