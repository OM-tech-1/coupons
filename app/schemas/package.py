from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
import re


class PackageBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=220)
    description: Optional[str] = None
    picture_url: Optional[str] = None
    brand: Optional[str] = Field(default=None, max_length=100, description="Brand name for the package")
    discount: Optional[float] = Field(default=None, ge=0, description="Discount percentage on the package")
    avg_rating: float = Field(default=0.0, ge=0, le=5, description="Average rating for the bundle")
    total_sold: int = Field(default=0, ge=0, description="Total bundles sold")
    category_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)

    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class PackageCreate(PackageBase):
    coupon_ids: List[UUID] = Field(default_factory=list, description="Coupons to include in this package")


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=220)
    description: Optional[str] = None
    picture_url: Optional[str] = None
    brand: Optional[str] = Field(default=None, max_length=100)
    discount: Optional[float] = Field(default=None, ge=0)
    avg_rating: Optional[float] = Field(default=None, ge=0, le=5)
    total_sold: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    coupon_ids: Optional[List[UUID]] = Field(default=None, description="Replace package coupons with this list")

    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class CouponInPackage(BaseModel):
    id: UUID
    title: str
    brand: Optional[str] = None
    discount_type: str
    discount_amount: float
    price: float = 0.0
    picture_url: Optional[str] = None
    pricing: Optional[Dict[str, Dict[str, float]]] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class CategoryInPackage(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class PackageResponse(PackageBase):
    id: UUID
    created_at: datetime
    max_saving: float = Field(default=0.0, description="Maximum saving (discount percentage)")
    pricing: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None, description="Auto-computed sum of coupon prices per currency"
    )
    total_price: Optional[Dict[str, float]] = Field(
        default=None, description="Total price per currency (sum of all coupon prices)"
    )
    category: Optional[CategoryInPackage] = None
    coupons: List[CouponInPackage] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PackageListResponse(PackageBase):
    """Lighter response for list endpoints (no nested coupons)."""
    id: UUID
    created_at: datetime
    max_saving: float = Field(default=0.0, description="Maximum saving (discount percentage)")
    pricing: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None, description="Auto-computed sum of coupon prices per currency"
    )
    total_price: Optional[Dict[str, float]] = Field(
        default=None, description="Total price per currency (sum of all coupon prices)"
    )
    category: Optional[CategoryInPackage] = None
    coupon_count: int = 0

    model_config = ConfigDict(from_attributes=True)
