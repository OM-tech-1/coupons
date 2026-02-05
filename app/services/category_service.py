from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models.category import Category
from app.models.coupon import Coupon
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM


class CategoryService:
    
    @staticmethod
    def create(db: Session, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        db_category = Category(
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            icon=category_data.icon,
            display_order=category_data.display_order,
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        # Invalidate category list cache
        invalidate_cache("categories:list:*")
        
        return db_category

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Category]:
        """Get all categories (cached)"""
        cache_k = cache_key("categories", "list", active_only)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        query = db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        categories = query.order_by(Category.display_order, Category.name).all()
        
        # Cache the result
        cache_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "icon": c.icon,
                "display_order": c.display_order,
                "is_active": c.is_active,
                "created_at": str(c.created_at) if c.created_at else None,
            }
            for c in categories
        ]
        set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        return categories

    @staticmethod
    def get_by_id(db: Session, category_id: UUID) -> Optional[Category]:
        """Get a category by its ID"""
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Category]:
        """Get a category by its slug"""
        return db.query(Category).filter(Category.slug == slug).first()

    @staticmethod
    def get_with_coupon_counts(db: Session, active_only: bool = True) -> List[dict]:
        """Get categories with active coupon counts"""
        query = db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        
        categories = query.order_by(Category.display_order, Category.name).all()
        
        result = []
        for cat in categories:
            coupon_count = db.query(Coupon).filter(
                and_(
                    Coupon.category_id == cat.id,
                    Coupon.is_active == True
                )
            ).count()
            
            result.append({
                "id": cat.id,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "icon": cat.icon,
                "display_order": cat.display_order,
                "is_active": cat.is_active,
                "created_at": cat.created_at,
                "coupon_count": coupon_count
            })
        
        return result

    @staticmethod
    def update(db: Session, category_id: UUID, category_data: CategoryUpdate) -> Optional[Category]:
        """Update a category"""
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return None
        
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        
        # Invalidate category caches
        invalidate_cache("categories:list:*")
        invalidate_cache(f"categories:id:{category_id}")
        invalidate_cache(f"categories:slug:*")
        
        return db_category

    @staticmethod
    def delete(db: Session, category_id: UUID) -> bool:
        """Delete a category"""
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return False
        
        db.delete(db_category)
        db.commit()
        
        # Invalidate category caches
        invalidate_cache("categories:list:*")
        invalidate_cache(f"categories:id:{category_id}")
        
        return True
