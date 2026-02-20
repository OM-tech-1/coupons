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
    picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryInPackage(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class PackageResponse(PackageBase):
    id: UUID
    created_at: datetime
    pricing: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None, description="Auto-computed sum of coupon prices per currency"
    )
    category: Optional[CategoryInPackage] = None
    coupons: List[CouponInPackage] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PackageListResponse(PackageBase):
    """Lighter response for list endpoints (no nested coupons)."""
    id: UUID
    created_at: datetime
    pricing: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None, description="Auto-computed sum of coupon prices per currency"
    )
    category: Optional[CategoryInPackage] = None
    coupon_count: int = 0

    model_config = ConfigDict(from_attributes=True)
