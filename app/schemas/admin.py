from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class AdminUserResponse(BaseModel):
    """User response with aggregated stats for admin"""
    id: UUID
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    # Aggregated stats
    total_orders: int = 0
    total_spent: float = 0.0
    
    class Config:
        from_attributes = True


class AdminOrderResponse(BaseModel):
    """Order response with user info for admin"""
    id: UUID
    user_id: UUID
    user_phone: Optional[str] = None
    user_name: Optional[str] = None
    total_amount: float
    status: str
    payment_method: Optional[str] = None
    created_at: datetime
    items_count: int = 0
    
    class Config:
        from_attributes = True


class PaginatedUsersResponse(BaseModel):
    """Paginated users list"""
    items: List[AdminUserResponse]
    total: int
    skip: int
    limit: int


class PaginatedOrdersResponse(BaseModel):
    """Paginated orders list"""
    items: List[AdminOrderResponse]
    total: int
    skip: int
    limit: int


class TopCouponResponse(BaseModel):
    """Top performing coupon stats"""
    id: UUID
    code: str
    title: str
    brand: Optional[str] = None
    total_sales: int = 0
    revenue: float = 0.0


class DashboardResponse(BaseModel):
    """Dashboard aggregated metrics"""
    # Revenue
    total_revenue: float = 0.0
    revenue_this_month: float = 0.0
    
    # Orders
    total_orders: int = 0
    completed_orders: int = 0
    pending_orders: int = 0
    
    # Users
    total_users: int = 0
    active_users: int = 0
    new_users_this_month: int = 0
    
    # Coupons
    total_coupons: int = 0
    active_coupons: int = 0
    
    # Top performing
    top_coupons: List[TopCouponResponse] = []
    
    # Recent orders
    recent_orders: List[AdminOrderResponse] = []
