from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.country import CountryCreate, CountryUpdate, CountryResponse
from app.schemas.coupon import CouponResponse
from app.services.country_service import CountryService
from app.services.coupon_service import CouponService
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[CountryResponse])
def list_countries(
    region_id: Optional[UUID] = Query(None, description="Filter by region ID"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List all countries with optional region filter (public endpoint)"""
    return CountryService.get_all(db, region_id=region_id, active_only=active_only)


@router.get("/{slug}", response_model=CountryResponse)
def get_country_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a country by its slug (public endpoint)"""
    country = CountryService.get_by_slug(db, slug)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with slug '{slug}' not found"
        )
    return country


@router.get("/{slug}/coupons", response_model=List[CouponResponse])
def get_coupons_in_country(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Browse coupons in a specific country (public endpoint)"""
    country = CountryService.get_by_slug(db, slug)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with slug '{slug}' not found"
        )
    
    return CouponService.get_all(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        country_id=country.id
    )


@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
def create_country(
    country: CountryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new country (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create countries"
        )
    
    # Check if slug or country_code already exists
    existing_slug = CountryService.get_by_slug(db, country.slug)
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country with slug '{country.slug}' already exists"
        )
    
    existing_code = CountryService.get_by_country_code(db, country.country_code)
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country with code '{country.country_code}' already exists"
        )
    
    return CountryService.create(db, country)


@router.put("/{country_id}", response_model=CountryResponse)
def update_country(
    country_id: UUID,
    country_data: CountryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a country (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update countries"
        )
    
    # Check for slug/code conflicts if being updated
    if country_data.slug:
        existing = CountryService.get_by_slug(db, country_data.slug)
        if existing and existing.id != country_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Country with slug '{country_data.slug}' already exists"
            )
    
    if country_data.country_code:
        existing = CountryService.get_by_country_code(db, country_data.country_code)
        if existing and existing.id != country_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Country with code '{country_data.country_code}' already exists"
            )
    
    country = CountryService.update(db, country_id, country_data)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Country not found"
        )
    return country


@router.delete("/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country(
    country_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a country (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete countries"
        )
    
    success = CountryService.delete(db, country_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Country not found"
        )
    return None
