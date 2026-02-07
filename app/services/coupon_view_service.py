from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.coupon_view import CouponView
from app.models.coupon import Coupon
from app.models.order import OrderItem, Order


class CouponViewService:
    
    @staticmethod
    def track_view(
        db: Session,
        coupon_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> CouponView:
        """Track a coupon view"""
        view = CouponView(
            coupon_id=coupon_id,
            user_id=user_id,
            session_id=session_id
        )
        db.add(view)
        db.commit()
        db.refresh(view)
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
        """Get comprehensive analytics for a single coupon"""
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
        
        return {
            "coupon_id": str(coupon_id),
            "code": coupon.code,
            "title": coupon.title,
            "brand": coupon.brand,
            "is_active": coupon.is_active,
            "total_views": total_views,
            "unique_viewers": unique_viewers,
            "total_redemptions": total_redemptions,
            "redemption_rate": redemption_rate,
            "views_last_7_days": views_last_7_days,
            "views_last_30_days": views_last_30_days
        }
    
    @staticmethod
    def get_all_coupons_analytics(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "views"  # views, redemptions, rate
    ) -> dict:
        """Get analytics for all coupons with pagination (optimized queries)"""
        # Get total count first
        total = db.query(func.count(Coupon.id)).scalar() or 0
        
        # Get coupons
        coupons = db.query(Coupon).offset(skip).limit(limit).all()
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
        
        # Build analytics list
        analytics = []
        for coupon in coupons:
            total_views = view_counts.get(coupon.id, 0)
            unique_viewers = unique_counts.get(coupon.id, 0)
            total_redemptions = redemption_counts.get(coupon.id, 0)
            
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
                "redemption_rate": redemption_rate
            })
        
        # Sort based on criteria
        if sort_by == "views":
            analytics.sort(key=lambda x: x["total_views"], reverse=True)
        elif sort_by == "redemptions":
            analytics.sort(key=lambda x: x["total_redemptions"], reverse=True)
        elif sort_by == "rate":
            analytics.sort(key=lambda x: x["redemption_rate"], reverse=True)
        
        return {
            "items": analytics,
            "total": total,
            "skip": skip,
            "limit": limit
        }

