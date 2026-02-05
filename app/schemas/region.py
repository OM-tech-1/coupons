from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import re


class RegionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    display_order: int = Field(default=0, ge=0)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly (lowercase, hyphens only)"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    
    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class RegionResponse(RegionBase):
    id: UUID
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


# Forward declaration for circular import
class CountryInRegion(BaseModel):
    """Simplified country info for nested in region responses"""
    id: UUID
    name: str
    slug: str
    country_code: str
    is_active: bool
    
    class Config:
        from_attributes = True


class RegionWithCountries(RegionResponse):
    """Region response with nested countries list"""
    countries: List[CountryInRegion] = []
