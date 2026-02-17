from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithCouponCount
from app.schemas.coupon import CouponResponse
from app.services.category_service import CategoryService
from app.services.category_service import CategoryService
from app.services.coupon_service import CouponService
from app.utils.security import get_current_user, get_current_user_optional
from app.utils.currency import get_currency_from_phone_code
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List all categories (public endpoint)"""
    return CategoryService.get_all(db, active_only=active_only)


@router.get("/with-counts", response_model=List[CategoryWithCouponCount])
def list_categories_with_counts(
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List categories with coupon counts (public endpoint for discovery pages)"""
    categories_data = CategoryService.get_with_coupon_counts(db, active_only=active_only)
    return categories_data


@router.get("/{slug}", response_model=CategoryResponse)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a category by its slug (public endpoint)"""
    category = CategoryService.get_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with slug '{slug}' not found"
        )
    return category


@router.get("/{slug}/coupons", response_model=List[CouponResponse])
def get_coupons_in_category(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Browse coupons in a specific category (public endpoint)"""
    category = CategoryService.get_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with slug '{slug}' not found"
        )
        
    currency_code = "USD"
    if current_user:
        currency_code = getattr(current_user, "context_currency", None) or get_currency_from_phone_code(current_user.phone_number)
    
    return CouponService.get_all(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        category_id=category.id,
        currency_code=currency_code
    )


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new category (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories"
        )
    
    # Check if slug already exists
    existing = CategoryService.get_by_slug(db, category.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{category.slug}' already exists"
        )
    
    return CategoryService.create(db, category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a category (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update categories"
        )
    
    # If updating slug, check for duplicates
    if category_data.slug:
        existing = CategoryService.get_by_slug(db, category_data.slug)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{category_data.slug}' already exists"
            )
    
    category = CategoryService.update(db, category_id, category_data)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a category (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete categories"
        )
    
    success = CategoryService.delete(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return None
