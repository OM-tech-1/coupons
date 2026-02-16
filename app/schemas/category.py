from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID
import re


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    display_order: int = Field(default=0, ge=0)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly (lowercase, hyphens only)"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    display_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    
    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class CategoryResponse(CategoryBase):
    id: UUID
    is_active: bool = True
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithCouponCount(CategoryResponse):
    """Category with count of active coupons"""
    coupon_count: int = 0
