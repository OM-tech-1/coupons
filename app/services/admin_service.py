from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, String, case
from uuid import UUID
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon
from app.schemas.admin import (
    AdminUserResponse, AdminOrderResponse, PaginatedUsersResponse,
    PaginatedOrdersResponse, DashboardResponse, TopCouponResponse,
    PerformanceResponse, PerformanceData
)
from app.models.coupon_view import CouponView
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_SHORT


class AdminService:
    
    @staticmethod
    def get_all_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 20,
        active_only: bool = False,
        search: Optional[str] = None
    ) -> PaginatedUsersResponse:
        """Get all users with aggregated order stats"""
        query = db.query(User)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        # Search by name or phone number
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    func.lower(User.full_name).like(func.lower(search_term)),
                    User.phone_number.like(search_term)
                )
            )
        
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
        user_id: Optional[UUID] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> PaginatedOrdersResponse:
        """Get all orders with filters and statistics"""
        query = db.query(Order)
        
        # Apply filters
        if status:
            query = query.filter(Order.status == status)
        if user_id:
            query = query.filter(Order.user_id == user_id)
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        # Search by order ID or user phone
        if search:
            search_term = f"%{search}%"
            # Join with User to search by phone
            query = query.join(User, Order.user_id == User.id).filter(
                or_(
                    func.cast(Order.id, String).like(search_term),
                    User.phone_number.like(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        total = query.count()
        
        # Get order statistics (on filtered set, excluding pagination)
        stats = db.query(
            func.coalesce(func.sum(
                case((Order.status == 'paid', Order.total_amount), else_=0)
            ), 0.0).label('total_revenue'),
            func.sum(case((Order.status == 'paid', 1), else_=0)).label('completed_count'),
            func.sum(case((Order.status == 'pending', 1), else_=0)).label('pending_count'),
            func.sum(case((Order.status == 'failed', 1), else_=0)).label('failed_count'),
            func.sum(case((Order.status == 'cancelled', 1), else_=0)).label('cancelled_count')
        ).first()
        
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
            limit=limit,
            total_revenue=float(stats.total_revenue or 0),
            completed_count=int(stats.completed_count or 0),
            pending_count=int(stats.pending_count or 0),
            failed_count=int(stats.failed_count or 0),
            cancelled_count=int(stats.cancelled_count or 0)
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
    def get_dashboard_stats(db: Session, refresh: bool = False) -> DashboardResponse:
        """Get aggregated dashboard statistics (cached 60s, optimized queries)"""
        cache_k = cache_key("admin", "dashboard")
        
        if not refresh:
            cached = get_cache(cache_k)
            if cached is not None:
                return cached
        
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # === QUERY 1: All order + revenue stats in ONE query ===
        order_stats = db.query(
            func.count(Order.id).label('total_orders'),
            func.count(case((Order.status == 'paid', 1))).label('completed_orders'),
            func.count(case((Order.status == 'pending', 1))).label('pending_orders'),
            func.coalesce(func.sum(case((Order.status == 'paid', Order.total_amount), else_=0.0)), 0.0).label('total_revenue'),
            func.coalesce(func.sum(case(
                (db.query(Order).filter(Order.status == 'paid', Order.created_at >= month_start).exists().correlate(Order), Order.total_amount),
                else_=0.0
            )), 0.0).label('revenue_this_month_placeholder'),
        ).first()
        
        total_orders = order_stats.total_orders
        completed_orders = order_stats.completed_orders
        pending_orders = order_stats.pending_orders
        total_revenue = float(order_stats.total_revenue)
        
        # Revenue this month (simpler separate query — avoids complex correlated subquery)
        revenue_this_month = float(db.query(
            func.coalesce(func.sum(Order.total_amount), 0.0)
        ).filter(Order.status == 'paid', Order.created_at >= month_start).scalar() or 0.0)
        
        # === QUERY 2: All user stats in ONE query ===
        user_stats = db.query(
            func.count(User.id).label('total'),
            func.count(case((User.is_active == True, 1))).label('active'),
            func.count(case((User.created_at >= month_start, 1))).label('new_this_month'),
        ).first()
        
        total_users = user_stats.total
        active_users = user_stats.active
        new_users_month = user_stats.new_this_month
        
        # === QUERY 3: Coupon stats in ONE query ===
        coupon_stats = db.query(
            func.count(Coupon.id).label('total'),
            func.count(case((Coupon.is_active == True, 1))).label('active'),
        ).first()
        
        total_coupons = coupon_stats.total
        active_coupons = coupon_stats.active
        
        # === QUERY 4: Top performing coupons ===
        top_coupons_query = db.query(
            Coupon.id, Coupon.code, Coupon.title, Coupon.brand,
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
        ).order_by(desc('total_sales')).limit(5).all()
        
        top_coupons = [
            TopCouponResponse(
                id=c.id, code=c.code, title=c.title, brand=c.brand,
                total_sales=c.total_sales, revenue=float(c.revenue)
            ) for c in top_coupons_query
        ]
        
        # === QUERY 5: Recent orders with JOIN (eliminates N+1) ===
        from sqlalchemy.orm import aliased
        items_subq = db.query(
            OrderItem.order_id,
            func.count(OrderItem.id).label('items_count')
        ).group_by(OrderItem.order_id).subquery()
        
        recent_rows = db.query(
            Order, User, func.coalesce(items_subq.c.items_count, 0).label('items_count')
        ).outerjoin(
            User, User.id == Order.user_id
        ).outerjoin(
            items_subq, items_subq.c.order_id == Order.id
        ).order_by(desc(Order.created_at)).limit(5).all()
        
        recent_orders = [
            AdminOrderResponse(
                id=order.id, user_id=order.user_id,
                user_phone=user.phone_number if user else None,
                user_name=user.full_name if user else None,
                total_amount=order.total_amount, status=order.status,
                payment_method=order.payment_method, created_at=order.created_at,
                items_count=items_count
            ) for order, user, items_count in recent_rows
        ]
        
        # === QUERY 6: Performance Graph (Views & Sales last 30 days) ===
        # Initialize dates map for last 30 days
        days_map = {}
        today = now.date()
        for i in range(30):
            d = today - timedelta(days=i)
            days_map[d] = {"views": 0, "sold": 0}
            
        start_date = now - timedelta(days=30)
        
        # Views query (group by day)
        views_query = db.query(
            func.date(CouponView.viewed_at).label('day'),
            func.count(CouponView.id).label('count')
        ).filter(
            CouponView.viewed_at >= start_date
        ).group_by('day').all()
        
        for row in views_query:
            if row.day in days_map:
                days_map[row.day]["views"] = row.count

        # Sales query (group by day)
        sales_query = db.query(
            func.date(Order.created_at).label('day'),
            func.count(Order.id).label('count')
        ).filter(
            Order.status == 'paid',
            Order.created_at >= start_date
        ).group_by('day').all()
        
        for row in sales_query:
            if row.day in days_map:
                days_map[row.day]["sold"] = row.count
        
        # Sort by date and create response objects
        sorted_dates = sorted(days_map.keys())
        views_list = [PerformanceData(date=str(d), count=days_map[d]["views"]) for d in sorted_dates]
        sold_list = [PerformanceData(date=str(d), count=days_map[d]["sold"]) for d in sorted_dates]
        
        performance = PerformanceResponse(views=views_list, sold=sold_list)

        result = DashboardResponse(
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
            recent_orders=recent_orders,
            performance=performance
        )
        
        # Cache as dict (Pydantic models can't be json.dumps'd directly)
        set_cache(cache_k, result.model_dump(mode='json'), CACHE_TTL_SHORT)
        return result
