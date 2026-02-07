from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from uuid import UUID
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon
from app.schemas.admin import (
    AdminUserResponse, AdminOrderResponse, PaginatedUsersResponse,
    PaginatedOrdersResponse, DashboardResponse, TopCouponResponse
)


class AdminService:
    
    @staticmethod
    def get_all_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 20,
        active_only: bool = False
    ) -> PaginatedUsersResponse:
        """Get all users with aggregated order stats"""
        query = db.query(User)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        # Get total count
        total = query.count()
        
        # Get users with pagination
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        
        # Build response with stats
        user_responses = []
        for user in users:
            # Get order stats for this user
            order_stats = db.query(
                func.count(Order.id).label('total_orders'),
                func.coalesce(func.sum(Order.total_amount), 0.0).label('total_spent')
            ).filter(
                Order.user_id == user.id,
                Order.status == 'paid'
            ).first()
            
            user_responses.append(AdminUserResponse(
                id=user.id,
                phone_number=user.phone_number,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                total_orders=order_stats.total_orders or 0,
                total_spent=float(order_stats.total_spent or 0.0)
            ))
        
        return PaginatedUsersResponse(
            items=user_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[AdminUserResponse]:
        """Get a single user with stats"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        order_stats = db.query(
            func.count(Order.id).label('total_orders'),
            func.coalesce(func.sum(Order.total_amount), 0.0).label('total_spent')
        ).filter(
            Order.user_id == user.id,
            Order.status == 'paid'
        ).first()
        
        return AdminUserResponse(
            id=user.id,
            phone_number=user.phone_number,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            total_orders=order_stats.total_orders or 0,
            total_spent=float(order_stats.total_spent or 0.0)
        )
    
    @staticmethod
    def get_all_orders(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> PaginatedOrdersResponse:
        """Get all orders with filters"""
        query = db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        total = query.count()
        
        orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
        
        order_responses = []
        for order in orders:
            # Get user info
            user = db.query(User).filter(User.id == order.user_id).first()
            # Get items count
            items_count = db.query(func.count(OrderItem.id)).filter(
                OrderItem.order_id == order.id
            ).scalar() or 0
            
            order_responses.append(AdminOrderResponse(
                id=order.id,
                user_id=order.user_id,
                user_phone=user.phone_number if user else None,
                user_name=user.full_name if user else None,
                total_amount=order.total_amount,
                status=order.status,
                payment_method=order.payment_method,
                created_at=order.created_at,
                items_count=items_count
            ))
        
        return PaginatedOrdersResponse(
            items=order_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    @staticmethod
    def get_order_by_id(db: Session, order_id: UUID) -> Optional[AdminOrderResponse]:
        """Get a single order by ID (admin - no user restriction)"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        user = db.query(User).filter(User.id == order.user_id).first()
        items_count = db.query(func.count(OrderItem.id)).filter(
            OrderItem.order_id == order.id
        ).scalar() or 0
        
        return AdminOrderResponse(
            id=order.id,
            user_id=order.user_id,
            user_phone=user.phone_number if user else None,
            user_name=user.full_name if user else None,
            total_amount=order.total_amount,
            status=order.status,
            payment_method=order.payment_method,
            created_at=order.created_at,
            items_count=items_count
        )
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> DashboardResponse:
        """Get aggregated dashboard statistics"""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Revenue stats
        total_revenue = db.query(
            func.coalesce(func.sum(Order.total_amount), 0.0)
        ).filter(Order.status == 'paid').scalar() or 0.0
        
        revenue_this_month = db.query(
            func.coalesce(func.sum(Order.total_amount), 0.0)
        ).filter(
            Order.status == 'paid',
            Order.created_at >= month_start
        ).scalar() or 0.0
        
        # Order stats
        total_orders = db.query(Order).count()
        completed_orders = db.query(Order).filter(Order.status == 'paid').count()
        pending_orders = db.query(Order).filter(Order.status == 'pending').count()
        
        # User stats
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        new_users_month = db.query(User).filter(User.created_at >= month_start).count()
        
        # Coupon stats
        total_coupons = db.query(Coupon).count()
        active_coupons = db.query(Coupon).filter(Coupon.is_active == True).count()
        
        # Top performing coupons (by sales count)
        top_coupons_query = db.query(
            Coupon.id,
            Coupon.code,
            Coupon.title,
            Coupon.brand,
            func.count(OrderItem.id).label('total_sales'),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0.0).label('revenue')
        ).join(
            OrderItem, OrderItem.coupon_id == Coupon.id
        ).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            Order.status == 'paid'
        ).group_by(
            Coupon.id, Coupon.code, Coupon.title, Coupon.brand
        ).order_by(
            desc('total_sales')
        ).limit(5).all()
        
        top_coupons = [
            TopCouponResponse(
                id=c.id,
                code=c.code,
                title=c.title,
                brand=c.brand,
                total_sales=c.total_sales,
                revenue=float(c.revenue)
            ) for c in top_coupons_query
        ]
        
        # Recent orders
        recent = db.query(Order).order_by(desc(Order.created_at)).limit(5).all()
        recent_orders = []
        for order in recent:
            user = db.query(User).filter(User.id == order.user_id).first()
            items_count = db.query(func.count(OrderItem.id)).filter(
                OrderItem.order_id == order.id
            ).scalar() or 0
            
            recent_orders.append(AdminOrderResponse(
                id=order.id,
                user_id=order.user_id,
                user_phone=user.phone_number if user else None,
                user_name=user.full_name if user else None,
                total_amount=order.total_amount,
                status=order.status,
                payment_method=order.payment_method,
                created_at=order.created_at,
                items_count=items_count
            ))
        
        return DashboardResponse(
            total_revenue=float(total_revenue),
            revenue_this_month=float(revenue_this_month),
            total_orders=total_orders,
            completed_orders=completed_orders,
            pending_orders=pending_orders,
            total_users=total_users,
            active_users=active_users,
            new_users_this_month=new_users_month,
            total_coupons=total_coupons,
            active_coupons=active_coupons,
            top_coupons=top_coupons,
            recent_orders=recent_orders
        )
