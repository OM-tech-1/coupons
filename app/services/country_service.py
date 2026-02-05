from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional

from app.models.country import Country
from app.schemas.country import CountryCreate, CountryUpdate
from app.cache import get_cache, set_cache, invalidate_cache, cache_key, CACHE_TTL_MEDIUM


class CountryService:
    
    @staticmethod
    def create(db: Session, country_data: CountryCreate) -> Country:
        """Create a new country"""
        db_country = Country(
            name=country_data.name,
            slug=country_data.slug,
            country_code=country_data.country_code,
            region_id=country_data.region_id,
        )
        db.add(db_country)
        db.commit()
        db.refresh(db_country)
        
        # Invalidate country list cache
        invalidate_cache("countries:list:*")
        invalidate_cache("regions:list:*")  # Also invalidate regions cache
        
        return db_country

    @staticmethod
    def get_all(db: Session, region_id: Optional[UUID] = None, active_only: bool = True) -> List[Country]:
        """Get all countries, optionally filtered by region (cached)"""
        cache_k = cache_key("countries", "list", str(region_id) if region_id else "all", active_only)
        cached = get_cache(cache_k)
        if cached is not None:
            return cached
        
        query = db.query(Country)
        if region_id:
            query = query.filter(Country.region_id == region_id)
        if active_only:
            query = query.filter(Country.is_active == True)
        countries = query.order_by(Country.name).all()
        
        # Cache the result
        cache_data = [
            {
                "id": str(c.id),
                "name": c.name,
                "slug": c.slug,
                "country_code": c.country_code,
                "region_id": str(c.region_id),
                "is_active": c.is_active,
                "created_at": str(c.created_at) if c.created_at else None,
            }
            for c in countries
        ]
        set_cache(cache_k, cache_data, CACHE_TTL_MEDIUM)
        
        return countries

    @staticmethod
    def get_by_region(db: Session, region_id: UUID, active_only: bool = True) -> List[Country]:
        """Get countries by region ID"""
        return CountryService.get_all(db, region_id=region_id, active_only=active_only)

    @staticmethod
    def get_by_id(db: Session, country_id: UUID) -> Optional[Country]:
        """Get a country by its ID"""
        return db.query(Country).filter(Country.id == country_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Country]:
        """Get a country by its slug"""
        return db.query(Country).filter(Country.slug == slug).first()

    @staticmethod
    def get_by_country_code(db: Session, country_code: str) -> Optional[Country]:
        """Get a country by its ISO country code"""
        return db.query(Country).filter(Country.country_code == country_code.upper()).first()

    @staticmethod
    def update(db: Session, country_id: UUID, country_data: CountryUpdate) -> Optional[Country]:
        """Update a country"""
        db_country = db.query(Country).filter(Country.id == country_id).first()
        if not db_country:
            return None
        
        update_data = country_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_country, field, value)
        
        db.commit()
        db.refresh(db_country)
        
        # Invalidate country caches
        invalidate_cache("countries:list:*")
        invalidate_cache(f"countries:id:{country_id}")
        invalidate_cache(f"countries:slug:*")
        invalidate_cache("regions:list:*")
        
        return db_country

    @staticmethod
    def delete(db: Session, country_id: UUID) -> bool:
        """Delete a country"""
        db_country = db.query(Country).filter(Country.id == country_id).first()
        if not db_country:
            return False
        
        db.delete(db_country)
        db.commit()
        
        # Invalidate country caches
        invalidate_cache("countries:list:*")
        invalidate_cache(f"countries:id:{country_id}")
        invalidate_cache("regions:list:*")
        
        return True
