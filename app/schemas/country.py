from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from uuid import UUID
import re


class CountryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 code")
    region_id: UUID
    
    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly (lowercase, hyphens only)"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    @validator('country_code')
    def validate_country_code(cls, v):
        """Ensure country code is uppercase 2-letter ISO code"""
        if not re.match(r'^[A-Z]{2}$', v.upper()):
            raise ValueError('Country code must be a 2-letter ISO 3166-1 alpha-2 code')
        return v.upper()


class CountryCreate(CountryBase):
    pass


class CountryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=120)
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    region_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    
    @validator('slug')
    def validate_slug(cls, v):
        if v is not None and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    @validator('country_code')
    def validate_country_code(cls, v):
        if v is not None and not re.match(r'^[A-Z]{2}$', v.upper()):
            raise ValueError('Country code must be a 2-letter ISO 3166-1 alpha-2 code')
        return v.upper() if v else None


class CountryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    country_code: str
    region_id: UUID
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class CountryWithRegion(CountryResponse):
    """Country response with nested region info"""
    region_name: Optional[str] = None
