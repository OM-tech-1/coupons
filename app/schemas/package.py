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
    expiration_date: Optional[datetime] = Field(default=None, description="Package expiration date")

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
    expiration_date: Optional[datetime] = Field(default=None, description="Package expiration date")
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
    # Multi-currency pricing for frontend
    prices: Dict[str, float] = Field(default_factory=dict, description="Prices in all supported currencies")
    discounts: Dict[str, float] = Field(default_factory=dict, description="Discount amounts in all supported currencies")

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to extract multi-currency pricing"""
        data = {
            'id': obj.id,
            'title': obj.title,
            'brand': obj.brand,
            'discount_type': obj.discount_type,
            'discount_amount': obj.discount_amount,
            'price': obj.price,
            'picture_url': obj.picture_url,
            'pricing': obj.pricing,
            'is_active': obj.is_active,
        }
        
        # Extract multi-currency pricing
        if obj.pricing and isinstance(obj.pricing, dict):
            prices = {}
            discounts = {}
            for currency, values in obj.pricing.items():
                if isinstance(values, dict):
                    prices[currency] = values.get('price', 0.0)
                    discounts[currency] = values.get('discount_amount', 0.0)
            data['prices'] = prices
            data['discounts'] = discounts
        else:
            data['prices'] = {'USD': obj.price or 0.0}
            data['discounts'] = {'USD': obj.discount_amount or 0.0}
        
        return cls(**data)

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
    # Flattened multi-currency fields for easier frontend access
    prices: Dict[str, float] = Field(default_factory=dict, description="Package prices in all supported currencies")
    final_prices: Dict[str, float] = Field(default_factory=dict, description="Final prices after discount in all currencies")
    
    category: Optional[CategoryInPackage] = None
    coupons: List[CouponInPackage] = Field(default_factory=list)

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to compute multi-currency pricing by summing coupon prices"""
        # First, convert coupons
        coupons = [CouponInPackage.from_orm(assoc.coupon) for assoc in obj.coupon_associations if assoc.coupon] if hasattr(obj, 'coupon_associations') else []
        
        data = {
            'id': obj.id,
            'name': obj.name,
            'slug': obj.slug,
            'description': obj.description,
            'picture_url': obj.picture_url,
            'brand': obj.brand,
            'discount': obj.discount,
            'avg_rating': obj.avg_rating,
            'total_sold': obj.total_sold,
            'category_id': obj.category_id,
            'is_active': obj.is_active,
            'is_featured': obj.is_featured,
            'expiration_date': obj.expiration_date,
            'created_at': obj.created_at,
            'max_saving': obj.discount or 0.0,
            'pricing': obj.pricing if hasattr(obj, 'pricing') else None,
            'total_price': obj.total_price if hasattr(obj, 'total_price') else None,
            'category': obj.category,
            'coupons': coupons,
        }
        
        # Compute multi-currency pricing by summing individual coupon prices
        prices = {}
        discounts = {}
        final_prices = {}
        
        # Sum up prices and discounts from all coupons in the package
        for coupon in coupons:
            # Sum prices for each currency
            for currency, price in coupon.prices.items():
                prices[currency] = prices.get(currency, 0.0) + price
            
            # Sum discounts for each currency
            for currency, discount in coupon.discounts.items():
                discounts[currency] = discounts.get(currency, 0.0) + discount
        
        # Calculate final prices after package discount
        if obj.discount:
            for currency, base_price in prices.items():
                final_prices[currency] = base_price * (1.0 - obj.discount / 100.0)
        else:
            final_prices = prices.copy()
        
        data['prices'] = prices
        data['discounts'] = discounts
        data['final_prices'] = final_prices
        
        return cls(**data)

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
    # Flattened multi-currency fields for easier frontend access
    prices: Dict[str, float] = Field(default_factory=dict, description="Package prices in all supported currencies")
    final_prices: Dict[str, float] = Field(default_factory=dict, description="Final prices after discount in all currencies")
    
    category: Optional[CategoryInPackage] = None
    coupon_count: int = 0

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to compute multi-currency pricing"""
        data = {
            'id': obj.id,
            'name': obj.name,
            'slug': obj.slug,
            'description': obj.description,
            'picture_url': obj.picture_url,
            'brand': obj.brand,
            'discount': obj.discount,
            'avg_rating': obj.avg_rating,
            'total_sold': obj.total_sold,
            'category_id': obj.category_id,
            'is_active': obj.is_active,
            'is_featured': obj.is_featured,
            'expiration_date': obj.expiration_date,
            'created_at': obj.created_at,
            'max_saving': obj.discount or 0.0,
            'pricing': obj.pricing if hasattr(obj, 'pricing') else None,
            'total_price': obj.total_price if hasattr(obj, 'total_price') else None,
            'category': obj.category,
            'coupon_count': len(obj.coupon_associations) if hasattr(obj, 'coupon_associations') else 0,
        }
        
        # Compute multi-currency pricing from pricing field
        prices = {}
        final_prices = {}
        
        if hasattr(obj, 'pricing') and obj.pricing and isinstance(obj.pricing, dict):
            for currency, values in obj.pricing.items():
                if isinstance(values, dict):
                    base_price = values.get('price', 0.0)
                    prices[currency] = base_price
                    # Apply discount if available
                    if obj.discount:
                        final_prices[currency] = base_price * (1.0 - obj.discount / 100.0)
                    else:
                        final_prices[currency] = base_price
        elif hasattr(obj, 'total_price') and obj.total_price and isinstance(obj.total_price, dict):
            # Fallback to total_price if pricing not available
            for currency, price in obj.total_price.items():
                prices[currency] = price
                if obj.discount:
                    final_prices[currency] = price * (1.0 - obj.discount / 100.0)
                else:
                    final_prices[currency] = price
        
        data['prices'] = prices
        data['final_prices'] = final_prices
        
        return cls(**data)

    model_config = ConfigDict(from_attributes=True)
