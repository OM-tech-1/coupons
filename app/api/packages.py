from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.package import PackageCreate, PackageUpdate, PackageResponse, PackageListResponse
from app.schemas.coupon import CouponPublicResponse
from app.services.package_service import PackageService
from app.utils.security import get_current_user, get_current_user_optional
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    data: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create packages")

    return PackageService.create(db, data)


@router.get("/", response_model=List[PackageListResponse])
def list_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    db: Session = Depends(get_db),
):
    return PackageService.get_all(
        db, skip=skip, limit=limit,
        category_id=category_id, is_active=is_active, is_featured=is_featured,
    )


@router.get("/{package_id}", response_model=PackageResponse)
def get_package(package_id: UUID, db: Session = Depends(get_db)):
    pkg = PackageService.get_by_id(db, package_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return pkg


@router.get("/{package_id}/coupons", response_model=List[CouponPublicResponse])
def get_package_coupons(package_id: UUID, db: Session = Depends(get_db)):
    from app.models.package import Package
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return PackageService.get_coupons(db, package_id)


@router.put("/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: UUID,
    data: PackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update packages")

    if data.slug:
        from app.models.package import Package
        existing = db.query(Package).filter(Package.slug == data.slug).first()
        if existing and existing.id != package_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Package with slug '{data.slug}' already exists")

    pkg = PackageService.update(db, package_id, data)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return pkg


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete packages")

    if not PackageService.delete(db, package_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return None


@router.post("/{package_id}/coupons", response_model=PackageResponse)
def add_coupons_to_package(
    package_id: UUID,
    coupon_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage package coupons")

    result = PackageService.add_coupons(db, package_id, coupon_ids)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return result


@router.delete("/{package_id}/coupons/{coupon_id}", response_model=PackageResponse)
def remove_coupon_from_package(
    package_id: UUID,
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage package coupons")

    result = PackageService.remove_coupon(db, package_id, coupon_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package or coupon association not found")
    return result
