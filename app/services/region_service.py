from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional

from app.models.region import Region
from app.models.country import Country
from app.schemas.region import RegionCreate, RegionUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM


class RegionService:
    
    @staticmethod
    def create(db: Session, region_data: RegionCreate) -> Region:
        """Create a new region"""
        db_region = Region(
            name=region_data.name,
            slug=region_data.slug,
            description=region_data.description,
            display_order=region_data.display_order,
        )
        db.add(db_region)
        db.commit()
        db.refresh(db_region)
        
        # Invalidate region list cache
        invalidate_cache("regions:list:*")
        
        return db_region

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Region]:
        """Get all regions (cached)"""
        cache_k = cache_key("regions", "list", active_only)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        query = db.query(Region)
        if active_only:
            query = query.filter(Region.is_active == True)
        regions = query.order_by(Region.display_order, Region.name).all()
        
        # Cache the result
        cache_data = [
            {
                "id": str(r.id),
                "name": r.name,
                "slug": r.slug,
                "description": r.description,
                "display_order": r.display_order,
                "is_active": r.is_active,
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in regions
        ]
        set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        return regions

    @staticmethod
    def get_all_with_countries(db: Session, active_only: bool = True) -> List[Region]:
        """Get all regions with their countries (eagerly loaded)"""
        query = db.query(Region).options(joinedload(Region.countries))
        if active_only:
            query = query.filter(Region.is_active == True)
        return query.order_by(Region.display_order, Region.name).all()

    @staticmethod
    def get_by_id(db: Session, region_id: UUID) -> Optional[Region]:
        """Get a region by its ID (cached)"""
        cache_k = cache_key("regions", "id", str(region_id))
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        region = db.query(Region).filter(Region.id == region_id).first()
        if region:
            cache_data = {
                "id": str(region.id), "name": region.name, "slug": region.slug,
                "description": region.description, "display_order": region.display_order,
                "is_active": region.is_active,
                "created_at": str(region.created_at) if region.created_at else None,
            }
            set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        return region

    @staticmethod
    def get_by_slug(db: Session, slug: str, with_countries: bool = False) -> Optional[Region]:
        """Get a region by its slug (cached)"""
        cache_k = cache_key("regions", "slug", slug, with_countries)
        cached = get_cache(cache_k)
        if cached is not None and not with_countries:
            return cached
        
        query = db.query(Region)
        if with_countries:
            query = query.options(joinedload(Region.countries))
        region = query.filter(Region.slug == slug).first()
        
        if region and not with_countries:
            cache_data = {
                "id": str(region.id), "name": region.name, "slug": region.slug,
                "description": region.description, "display_order": region.display_order,
                "is_active": region.is_active,
                "created_at": str(region.created_at) if region.created_at else None,
            }
            set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        return region

    @staticmethod
    def update(db: Session, region_id: UUID, region_data: RegionUpdate) -> Optional[Region]:
        """Update a region"""
        db_region = db.query(Region).filter(Region.id == region_id).first()
        if not db_region:
            return None
        
        update_data = region_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_region, field, value)
        
        db.commit()
        db.refresh(db_region)
        
        # Invalidate region caches
        invalidate_cache("regions:list:*")
        invalidate_cache(f"regions:id:{region_id}")
        invalidate_cache(f"regions:slug:*")
        
        return db_region

    @staticmethod
    def delete(db: Session, region_id: UUID) -> bool:
        """Delete a region"""
        db_region = db.query(Region).filter(Region.id == region_id).first()
        if not db_region:
            return False
        
        db.delete(db_region)
        db.commit()
        
        # Invalidate region caches
        invalidate_cache("regions:list:*")
        invalidate_cache(f"regions:id:{region_id}")
        
        return True
