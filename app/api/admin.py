from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminUserResponse, AdminOrderResponse,
    PaginatedUsersResponse, PaginatedOrdersResponse,
    DashboardResponse
)

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============== Dashboard ==============

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get aggregated dashboard statistics"""
    return AdminService.get_dashboard_stats(db)


# ============== User Management ==============

@router.get("/users", response_model=PaginatedUsersResponse)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users with order statistics"""
    return AdminService.get_all_users(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get specific user details with stats"""
    user = AdminService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: UUID,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Activate or deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


# ============== Order Management ==============

@router.get("/orders", response_model=PaginatedOrdersResponse)
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: pending, paid, failed, cancelled"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all orders with filters"""
    return AdminService.get_all_orders(db, skip=skip, limit=limit, status=status, user_id=user_id)


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get specific order details"""
    order = AdminService.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


# ============== Coupon Analytics ==============

@router.get("/analytics/coupons")
def get_coupons_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("views", pattern="^(views|redemptions|rate)$", description="Sort by: views, redemptions, rate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get analytics for all coupons (views, redemptions, rates)"""
    from app.services.coupon_view_service import CouponViewService
    return CouponViewService.get_all_coupons_analytics(db, skip=skip, limit=limit, sort_by=sort_by)


@router.get("/analytics/coupons/{coupon_id}")
def get_coupon_analytics(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get detailed analytics for a specific coupon"""
    from app.services.coupon_view_service import CouponViewService
    analytics = CouponViewService.get_coupon_analytics(db, coupon_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    return analytics
