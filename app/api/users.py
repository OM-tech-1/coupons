from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.security import get_current_user, verify_password, get_password_hash
from app.models.user import User
from app.schemas.user_coupon import UserCouponResponse
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_coupon_service import UserCouponService

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile (requires password verification)"""
    # Verify current password
    if not verify_password(profile_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Update fields that were provided
    update_data = profile_data.model_dump(exclude_unset=True, exclude={"current_password", "new_password"})
    
    for field, value in update_data.items():
        if value is not None:
            setattr(current_user, field, value)
    
    # Handle password change if requested
    if profile_data.new_password:
        current_user.hashed_password = get_password_hash(profile_data.new_password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/coupons", response_model=List[UserCouponResponse])
def get_my_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all coupons claimed by the current user"""
    return UserCouponService.get_user_coupons(db, current_user.id)
