from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.coupon_view import CouponView
from app.models.coupon import Coupon
from app.models.order import OrderItem, Order
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_SHORT, CACHE_TTL_MEDIUM


class CouponViewService:
    
    @staticmethod
    def track_view(
        db: Session,
        coupon_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> CouponView:
        """Track a coupon view and invalidate related analytics caches"""
        view = CouponView(
            coupon_id=coupon_id,
            user_id=user_id,
            session_id=session_id
        )
        db.add(view)
        db.commit()
        db.refresh(view)
        
        # Invalidate analytics caches affected by new views
        invalidate_cache(f"analytics:coupon:{coupon_id}")
        invalidate_cache("analytics:quick-stats")
        invalidate_cache("analytics:coupons:*")
        
        return view
    
    @staticmethod
    def get_view_count(db: Session, coupon_id: UUID) -> int:
        """Get total view count for a coupon"""
        return db.query(func.count(CouponView.id)).filter(
            CouponView.coupon_id == coupon_id
        ).scalar() or 0
    
    @staticmethod
    def get_unique_viewers(db: Session, coupon_id: UUID) -> int:
        """Get unique viewer count (by user_id or session_id)"""
        # Count unique user_ids (excluding None)
        user_count = db.query(func.count(func.distinct(CouponView.user_id))).filter(
            CouponView.coupon_id == coupon_id,
            CouponView.user_id.isnot(None)
        ).scalar() or 0
        
        # Count unique session_ids where user_id is None
        session_count = db.query(func.count(func.distinct(CouponView.session_id))).filter(
            CouponView.coupon_id == coupon_id,
            CouponView.user_id.is_(None),
            CouponView.session_id.isnot(None)
        ).scalar() or 0
        
        return user_count + session_count
    
    @staticmethod
    def get_views_in_period(db: Session, coupon_id: UUID, days: int = 7) -> int:
        """Get view count in the last N days"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(func.count(CouponView.id)).filter(
            CouponView.coupon_id == coupon_id,
            CouponView.viewed_at >= since
        ).scalar() or 0
    
    @staticmethod
    def get_redemption_count(db: Session, coupon_id: UUID) -> int:
        """Get total redemptions (purchases) for a coupon"""
        return db.query(func.count(OrderItem.id)).join(
            Order, Order.id == OrderItem.order_id
        ).filter(
            OrderItem.coupon_id == coupon_id,
            Order.status == 'paid'
        ).scalar() or 0
    
    @staticmethod
    def get_coupon_analytics(db: Session, coupon_id: UUID) -> dict:
        """Get comprehensive analytics for a single coupon (cached 5 min)"""
        cache_k = cache_key("analytics", "coupon", str(coupon_id))
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return None
        
        total_views = CouponViewService.get_view_count(db, coupon_id)
        unique_viewers = CouponViewService.get_unique_viewers(db, coupon_id)
        total_redemptions = CouponViewService.get_redemption_count(db, coupon_id)
        views_last_7_days = CouponViewService.get_views_in_period(db, coupon_id, 7)
        views_last_30_days = CouponViewService.get_views_in_period(db, coupon_id, 30)
        
        # Calculate redemption rate
        redemption_rate = 0.0
        if unique_viewers > 0:
            redemption_rate = round((total_redemptions / unique_viewers) * 100, 2)
        
        # Revenue for this coupon
        revenue = db.query(
            func.coalesce(func.sum(OrderItem.price), 0.0)
        ).join(Order, Order.id == OrderItem.order_id).filter(
            OrderItem.coupon_id == coupon_id,
            Order.status == 'paid'
        ).scalar() or 0.0
        
        # Daily performance trend (last 30 days)
        from sqlalchemy import cast, Date
        start_date = datetime.utcnow() - timedelta(days=30)
        
        daily_views = db.query(
            cast(CouponView.viewed_at, Date).label('date'),
            func.count(CouponView.id).label('count')
        ).filter(
            CouponView.coupon_id == coupon_id,
            CouponView.viewed_at >= start_date
        ).group_by(cast(CouponView.viewed_at, Date)).order_by('date').all()
        
        daily_sold = db.query(
            cast(Order.created_at, Date).label('date'),
            func.count(OrderItem.id).label('count')
        ).join(OrderItem, Order.id == OrderItem.order_id).filter(
            OrderItem.coupon_id == coupon_id,
            Order.status == 'paid',
            Order.created_at >= start_date
        ).group_by(cast(Order.created_at, Date)).order_by('date').all()
        
        result = {
            "coupon_id": str(coupon_id),
            "code": coupon.code,
            "title": coupon.title,
            "brand": coupon.brand,
            "is_active": coupon.is_active,
            "total_views": total_views,
            "unique_viewers": unique_viewers,
            "total_redemptions": total_redemptions,
            "sold_count": total_redemptions,
            "redemption_rate": redemption_rate,
            "conversion_rate": redemption_rate,
            "revenue": float(revenue),
            "views_last_7_days": views_last_7_days,
            "views_last_30_days": views_last_30_days,
            "performance": {
                "views": [{"date": str(v.date), "count": v.count} for v in daily_views],
                "sold": [{"date": str(s.date), "count": s.count} for s in daily_sold]
            }
        }
        
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
    
    @staticmethod
    def get_all_coupons_analytics(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "views",  # views, redemptions, rate
        category_id: Optional[UUID] = None,
        active_only: bool = False,
        search: Optional[str] = None
    ) -> dict:
        """Get analytics for all coupons with pagination and filtering (cached 5 min)"""
        # Include filters in cache key to avoid collisions
        cache_k = cache_key("analytics", "coupons", skip, limit, sort_by, str(category_id), str(active_only), str(search))
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        # Base query
        query = db.query(Coupon)
        
        # Apply filters
        if active_only:
            query = query.filter(Coupon.is_active == True)
        
        if category_id:
            query = query.filter(Coupon.category_id == category_id)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Coupon.title.ilike(search_term),
                    Coupon.code.ilike(search_term),
                    Coupon.brand.ilike(search_term)
                )
            )
        
        # Get total count first (after filtering)
        total = query.with_entities(func.count(Coupon.id)).scalar() or 0
        
        # Get coupons (paginated)
        coupons = query.offset(skip).limit(limit).all()
        coupon_ids = [c.id for c in coupons]
        
        if not coupon_ids:
            return {"items": [], "total": total, "skip": skip, "limit": limit}
        
        # Bulk query: Get view counts per coupon
        view_counts = dict(
            db.query(CouponView.coupon_id, func.count(CouponView.id))
            .filter(CouponView.coupon_id.in_(coupon_ids))
            .group_by(CouponView.coupon_id)
            .all()
        )
        
        # Bulk query: Get unique viewer counts (simplified - just unique session_ids)
        unique_counts = dict(
            db.query(CouponView.coupon_id, func.count(func.distinct(CouponView.session_id)))
            .filter(CouponView.coupon_id.in_(coupon_ids))
            .group_by(CouponView.coupon_id)
            .all()
        )
        
        # Bulk query: Get redemption counts
        redemption_counts = dict(
            db.query(OrderItem.coupon_id, func.count(OrderItem.id))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.coupon_id.in_(coupon_ids), Order.status == 'paid')
            .group_by(OrderItem.coupon_id)
            .all()
        )
        
        # Bulk query: Get revenue per coupon
        revenue_data = dict(
            db.query(OrderItem.coupon_id, func.coalesce(func.sum(OrderItem.price), 0.0))
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.coupon_id.in_(coupon_ids), Order.status == 'paid')
            .group_by(OrderItem.coupon_id)
            .all()
        )
        
        # Build analytics list
        analytics = []
        for coupon in coupons:
            total_views = view_counts.get(coupon.id, 0)
            unique_viewers = unique_counts.get(coupon.id, 0)
            total_redemptions = redemption_counts.get(coupon.id, 0)
            coupon_revenue = float(revenue_data.get(coupon.id, 0))
            
            redemption_rate = 0.0
            if unique_viewers > 0:
                redemption_rate = round((total_redemptions / unique_viewers) * 100, 2)
            
            analytics.append({
                "coupon_id": str(coupon.id),
                "code": coupon.code,
                "title": coupon.title,
                "brand": coupon.brand,
                "is_active": coupon.is_active,
                "total_views": total_views,
                "unique_viewers": unique_viewers,
                "total_redemptions": total_redemptions,
                "sold_count": total_redemptions,
                "redemption_rate": redemption_rate,
                "conversion_rate": redemption_rate,
                "revenue": coupon_revenue
            })
        
        # Sort based on criteria
        if sort_by == "views":
            analytics.sort(key=lambda x: x["total_views"], reverse=True)
        elif sort_by == "redemptions":
            analytics.sort(key=lambda x: x["total_redemptions"], reverse=True)
        elif sort_by == "rate":
            analytics.sort(key=lambda x: x["redemption_rate"], reverse=True)
        
        result = {
            "items": analytics,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
    
    @staticmethod
    def get_quick_stats(db: Session) -> dict:
        """Get today's quick stats for dashboard (cached 60s)"""
        cache_k = cache_key("analytics", "quick-stats")
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today's views
        todays_views = db.query(func.count(CouponView.id)).filter(
            CouponView.viewed_at >= today_start
        ).scalar() or 0
        
        # Today's redemptions
        todays_redemptions = db.query(func.count(OrderItem.id)).join(
            Order, Order.id == OrderItem.order_id
        ).filter(Order.status == 'paid', Order.created_at >= today_start).scalar() or 0
        
        # Unique viewers today
        todays_unique = db.query(func.count(func.distinct(CouponView.session_id))).filter(
            CouponView.viewed_at >= today_start
        ).scalar() or 0
        
        todays_conv = round((todays_redemptions / todays_unique) * 100, 2) if todays_unique > 0 else 0.0
        
        # Overall stats
        total_views = db.query(func.count(CouponView.id)).scalar() or 0
        total_redemptions = db.query(func.count(OrderItem.id)).join(
            Order, Order.id == OrderItem.order_id
        ).filter(Order.status == 'paid').scalar() or 0
        total_unique = db.query(func.count(func.distinct(CouponView.session_id))).scalar() or 0
        avg_rate = round((total_redemptions / total_unique) * 100, 2) if total_unique > 0 else 0.0
        
        result = {
            "today": {"views": todays_views, "redemptions": todays_redemptions, "conversion_rate": todays_conv},
            "overall": {"total_views": total_views, "total_redemptions": total_redemptions, "avg_redemption_rate": avg_rate}
        }
        
        set_cache(cache_k, result, CACHE_TTL_SHORT)
        return result
    
    @staticmethod
    def get_trends(db: Session, days: int = 30) -> dict:
        """Get daily trends for views and redemptions (cached 5 min)"""
        cache_k = cache_key("analytics", "trends", days)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        from sqlalchemy import cast, Date
        start_date = datetime.utcnow() - timedelta(days=days)
        
        daily_views = db.query(
            cast(CouponView.viewed_at, Date).label('date'),
            func.count(CouponView.id).label('count')
        ).filter(CouponView.viewed_at >= start_date).group_by(
            cast(CouponView.viewed_at, Date)
        ).order_by('date').all()
        
        daily_redemptions = db.query(
            cast(Order.created_at, Date).label('date'),
            func.count(OrderItem.id).label('count')
        ).join(OrderItem, Order.id == OrderItem.order_id).filter(
            Order.status == 'paid', Order.created_at >= start_date
        ).group_by(cast(Order.created_at, Date)).order_by('date').all()
        
        result = {
            "period_days": days,
            "views": [{"date": str(v.date), "count": v.count} for v in daily_views],
            "redemptions": [{"date": str(r.date), "count": r.count} for r in daily_redemptions]
        }
        
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
    
    @staticmethod
    def get_category_performance(db: Session) -> list:
        """Get performance stats grouped by category (cached 5 min)"""
        cache_k = cache_key("analytics", "categories")
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        from app.models.category import Category
        categories = db.query(Category).filter(Category.is_active == True).all()
        
        result = []
        for cat in categories:
            coupon_ids = [c[0] for c in db.query(Coupon.id).filter(Coupon.category_id == cat.id).all()]
            if not coupon_ids:
                result.append({"category_id": str(cat.id), "category_name": cat.name, "coupon_count": 0, "views": 0, "redemptions": 0, "revenue": 0.0})
                continue
            
            views = db.query(func.count(CouponView.id)).filter(CouponView.coupon_id.in_(coupon_ids)).scalar() or 0
            stats = db.query(
                func.count(OrderItem.id).label('redemptions'),
                func.coalesce(func.sum(OrderItem.price), 0.0).label('revenue')
            ).join(Order, Order.id == OrderItem.order_id).filter(
                OrderItem.coupon_id.in_(coupon_ids), Order.status == 'paid'
            ).first()
            
            result.append({"category_id": str(cat.id), "category_name": cat.name, "coupon_count": len(coupon_ids),
                          "views": views, "redemptions": stats.redemptions or 0, "revenue": float(stats.revenue or 0)})
        
        result.sort(key=lambda x: x['revenue'], reverse=True)
        
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
    
    @staticmethod
    def get_monthly_stats(db: Session, months: int = 12) -> list:
        """Get monthly orders and revenue (cached 5 min)"""
        cache_k = cache_key("analytics", "monthly", months)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        from sqlalchemy import extract
        result = []
        now = datetime.utcnow()
        
        for i in range(months):
            month_date = now - timedelta(days=30 * i)
            year, month = month_date.year, month_date.month
            
            stats = db.query(
                func.count(Order.id).label('orders'),
                func.coalesce(func.sum(Order.total_amount), 0.0).label('revenue')
            ).filter(
                Order.status == 'paid',
                extract('year', Order.created_at) == year,
                extract('month', Order.created_at) == month
            ).first()
            
            result.append({"year": year, "month": month, "month_name": month_date.strftime("%B"),
                          "orders": stats.orders or 0, "revenue": float(stats.revenue or 0)})
        
        result.reverse()
        
        set_cache(cache_k, result, CACHE_TTL_MEDIUM)
        return result
