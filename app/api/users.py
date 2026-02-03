from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.schemas.user_coupon import UserCouponResponse
from app.services.user_coupon_service import UserCouponService

router = APIRouter()


@router.get("/coupons", response_model=List[UserCouponResponse])
def get_my_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all coupons claimed by the current user"""
    return UserCouponService.get_user_coupons(db, current_user.id)
