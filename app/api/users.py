from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.utils.security import get_current_user, verify_password, get_password_hash
from app.models.user import User
from app.schemas.user_coupon import (
    UserCouponResponse,
    WalletSummaryResponse,
    WalletCouponResponse,
    UserCouponDetailResponse,
)
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
    """Update current user's profile"""
    
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


@router.get("/coupons/{coupon_id}", response_model=UserCouponDetailResponse)
def get_my_coupon_detail(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed view of a specific coupon owned by the current user"""
    detail = UserCouponService.get_user_coupon_detail(db, current_user.id, coupon_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found in your collection"
        )
    return detail


@router.get("/wallet", response_model=WalletSummaryResponse)
def get_my_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get wallet summary: total coupons, active, used, expired counts"""
    return UserCouponService.get_wallet_summary(db, current_user.id)


@router.get("/wallet/coupons", response_model=List[WalletCouponResponse])
def get_wallet_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all coupons in the user's wallet with purchase and expiry dates"""
    return UserCouponService.get_wallet_coupons(db, current_user.id)


@router.post("/coupons/{coupon_id}/mark-used", response_model=UserCouponDetailResponse)
def mark_coupon_used(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a coupon as used/redeemed"""
    result = UserCouponService.mark_coupon_as_used(db, current_user.id, coupon_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found in your collection"
        )
    return result

