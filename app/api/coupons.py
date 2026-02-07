from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse
from app.services.coupon_service import CouponService
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
def create_coupon(
    coupon: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new coupon (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create coupons"
        )
    
    # Check if code already exists
    existing = CouponService.get_by_code(db, coupon.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon code already exists"
        )
    
    return CouponService.create(db, coupon)


@router.get("/", response_model=List[CouponResponse])
def list_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    region_id: Optional[UUID] = Query(None, description="Filter by region ID"),
    country_id: Optional[UUID] = Query(None, description="Filter by country ID"),
    availability_type: Optional[str] = Query(None, pattern="^(online|local|both)$", description="Filter by availability type"),
    search: Optional[str] = Query(None, description="Search by title, brand, or code"),
    db: Session = Depends(get_db)
):
    """List all coupons with optional filters (public endpoint with enhanced filtering)"""
    return CouponService.get_all(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        category_id=category_id,
        region_id=region_id,
        country_id=country_id,
        availability_type=availability_type,
        search=search
    )


@router.get("/{coupon_id}", response_model=CouponResponse)
def get_coupon(coupon_id: UUID, db: Session = Depends(get_db)):
    """Get a coupon by ID"""
    coupon = CouponService.get_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    return coupon


@router.put("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: UUID,
    coupon_data: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a coupon (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update coupons"
        )
    
    # If updating code, check for duplicates
    if coupon_data.code:
        existing = CouponService.get_by_code(db, coupon_data.code)
        if existing and existing.id != coupon_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon code already exists"
            )
    
    coupon = CouponService.update(db, coupon_id, coupon_data)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    return coupon


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a coupon (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete coupons"
        )
    
    success = CouponService.delete(db, coupon_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    return None


@router.post("/{coupon_id}/claim", status_code=status.HTTP_201_CREATED)
def claim_coupon(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Claim a coupon for the current user"""
    from app.services.user_coupon_service import UserCouponService
    
    user_coupon, message = UserCouponService.claim_coupon(db, current_user.id, coupon_id)
    if not user_coupon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {"message": message, "coupon_id": str(coupon_id)}


@router.post("/{coupon_id}/view", status_code=status.HTTP_201_CREATED)
def track_coupon_view(
    coupon_id: UUID,
    session_id: Optional[str] = Query(None, description="Session ID for anonymous tracking"),
    db: Session = Depends(get_db)
):
    """Track a coupon view (public endpoint - no auth required)"""
    from app.services.coupon_view_service import CouponViewService
    from app.services.coupon_service import CouponService
    
    # Verify coupon exists
    coupon = CouponService.get_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    # Note: For authenticated user tracking, frontend should pass session_id
    # which can be the user_id from their JWT token. This keeps the endpoint
    # simple and doesn't require parsing auth headers optionally.
    CouponViewService.track_view(db, coupon_id, user_id=None, session_id=session_id)
    return {"message": "View tracked", "coupon_id": str(coupon_id)}

