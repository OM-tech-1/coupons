from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID as PyUUID
from app.config import JWT_SECRET, JWT_ALGORITHM
from app.database import get_db
from app.models.user import User
from app.cache import get_cache, set_cache, cache_key, invalidate_cache, CACHE_TTL_SHORT

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=32768,
    argon2__time_cost=2,
    argon2__parallelism=2
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def invalidate_user_cache(user_id: str):
    """Call this when user profile is updated."""
    invalidate_cache(f"user:auth:{user_id}")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Decode JWT token and return current user (Redis-cached)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check Redis cache - if user was recently fetched, load by cached PK (still fast but validates existence)
    ck = cache_key("user", "auth", user_id)
    cached = get_cache(ck)

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Cache the user marker if not already cached
    if cached is None:
        set_cache(ck, {"id": str(user.id)}, CACHE_TTL_SHORT)

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
