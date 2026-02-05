from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.region import RegionCreate, RegionUpdate, RegionResponse, RegionWithCountries
from app.schemas.coupon import CouponResponse
from app.services.region_service import RegionService
from app.services.coupon_service import CouponService
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[RegionWithCountries])
def list_regions_with_countries(
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List all regions with nested countries (public endpoint for discovery)"""
    return RegionService.get_all_with_countries(db, active_only=active_only)


@router.get("/{slug}", response_model=RegionWithCountries)
def get_region_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a region by its slug with countries (public endpoint)"""
    region = RegionService.get_by_slug(db, slug, with_countries=True)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with slug '{slug}' not found"
        )
    return region


@router.get("/{slug}/coupons", response_model=List[CouponResponse])
def get_coupons_in_region(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Browse coupons in a specific region (public endpoint)"""
    region = RegionService.get_by_slug(db, slug)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with slug '{slug}' not found"
        )
    
    return CouponService.get_all(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        region_id=region.id
    )


@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
def create_region(
    region: RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new region (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create regions"
        )
    
    # Check if slug already exists
    existing = RegionService.get_by_slug(db, region.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Region with slug '{region.slug}' already exists"
        )
    
    return RegionService.create(db, region)


@router.put("/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: UUID,
    region_data: RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a region (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update regions"
        )
    
    # If updating slug, check for duplicates
    if region_data.slug:
        existing = RegionService.get_by_slug(db, region_data.slug)
        if existing and existing.id != region_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Region with slug '{region_data.slug}' already exists"
            )
    
    region = RegionService.update(db, region_id, region_data)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return region


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(
    region_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a region (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete regions"
        )
    
    success = RegionService.delete(db, region_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return None
