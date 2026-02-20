from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse, CouponPublicResponse
from app.services.coupon_service import CouponService
from app.utils.security import get_current_user, get_current_user_optional
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


@router.get("/", response_model=List[CouponPublicResponse])
def list_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    region_id: Optional[UUID] = Query(None, description="Filter by region ID"),
    country_id: Optional[UUID] = Query(None, description="Filter by country ID"),
    availability_type: Optional[str] = Query(None, pattern="^(online|local|both)$", description="Filter by availability type"),
    search: Optional[str] = Query(None, description="Search by title, brand, or code"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    min_discount: Optional[float] = Query(None, ge=0, description="Filter by minimum discount amount"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return CouponService.get_all(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        category_id=category_id,
        region_id=region_id,
        country_id=country_id,
        availability_type=availability_type,
        search=search,
        is_featured=is_featured,
        min_discount=min_discount,
    )


@router.get("/trending", response_model=List[CouponPublicResponse])
def get_trending_coupons(
    period: str = Query("24h", pattern="^(24h|7d)$", description="Trending period: 24h or 7d"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending coupons ranked by real-time view count"""
    from app.services.redis_service import RedisService
    return RedisService.get_trending_coupons(db, period=period, limit=limit)


@router.get("/recently-viewed", response_model=List[CouponPublicResponse])
def get_recently_viewed(
    session_id: str = Query(..., description="Session or user ID"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get recently viewed coupons for a session/user"""
    from app.services.redis_service import RedisService
    return RedisService.get_recently_viewed(db, session_id=session_id, limit=limit)


@router.get("/featured", response_model=List[CouponPublicResponse])
def get_featured_coupons(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured coupons for homepage (fast cached response)"""
    from app.services.redis_service import RedisService
    return RedisService.get_featured_coupons(db, limit=limit)


@router.get("/{coupon_id}", response_model=CouponPublicResponse)
def get_coupon(
    coupon_id: UUID, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
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
    from app.services.redis_service import RedisService
    
    # Verify coupon exists
    coupon = CouponService.get_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    # Track view in DB
    CouponViewService.track_view(db, coupon_id, user_id=None, session_id=session_id)
    
    # Feed Redis trending + recently viewed
    coupon_id_str = str(coupon_id)
    RedisService.record_trending_view(coupon_id_str)
    if session_id:
        RedisService.record_recently_viewed(session_id, coupon_id_str)
    
    return {"message": "View tracked", "coupon_id": coupon_id_str}


@router.get("/{coupon_id}/stock")
def get_coupon_stock(
    coupon_id: UUID,
    db: Session = Depends(get_db)
):
    """Get real-time stock count for a coupon (Redis-powered)"""
    from app.services.redis_service import RedisService
    
    result = RedisService.get_stock(db, str(coupon_id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    return result

