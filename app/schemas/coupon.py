from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID


class CouponBasePublic(BaseModel):
    brand: Optional[str] = Field(default=None, max_length=100, description="Brand/company name")
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    discount_type: str = Field(default="percentage", pattern="^(percentage|fixed)$")
    discount_amount: float = Field(..., gt=0)
    price: float = Field(default=0.0, ge=0, description="Price to purchase this coupon")
    min_purchase: float = Field(default=0.0, ge=0)
    max_uses: Optional[int] = Field(default=None, ge=1)
    expiration_date: Optional[datetime] = None
    # New fields for stock and featured
    stock: Optional[int] = Field(default=None, ge=0, description="Available stock (null = unlimited)")
    is_featured: bool = Field(default=False, description="Featured on homepage")
    is_active: bool = Field(default=True, description="Whether coupon is active")
    picture_url: Optional[str] = None
    # Fields for categories and geography
    category_id: Optional[UUID] = None
    availability_type: str = Field(default="online", pattern="^(online|local|both)$")
    country_ids: List[UUID] = Field(default_factory=list)
    pricing: Optional[Dict[str, Dict[str, float]]] = Field(default=None, description="Multi-currency pricing e.g. {'INR': {'price': 100, 'discount_amount': 50}}")
    is_package_coupon: bool = Field(default=False, description="Whether this coupon belongs to a package")


class CouponBase(CouponBasePublic):
    code: str = Field(..., min_length=3, max_length=50)
    redeem_code: Optional[str] = Field(default=None, max_length=100, description="Actual code revealed after purchase")


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=3, max_length=50)
    redeem_code: Optional[str] = Field(default=None, max_length=100)
    brand: Optional[str] = Field(default=None, max_length=100)
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = None
    discount_type: Optional[str] = Field(default=None, pattern="^(percentage|fixed)$")
    discount_amount: Optional[float] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, ge=0)  # Allow price updates
    min_purchase: Optional[float] = Field(default=None, ge=0)
    max_uses: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None
    picture_url: Optional[str] = None
    expiration_date: Optional[datetime] = None
    # New fields for stock and featured
    stock: Optional[int] = Field(default=None, ge=0)
    is_featured: Optional[bool] = None
    # Optional fields for categories/geography
    category_id: Optional[UUID] = None
    availability_type: Optional[str] = Field(default=None, pattern="^(online|local|both)$")
    country_ids: Optional[List[UUID]] = None
    pricing: Optional[Dict[str, Dict[str, float]]] = None
    is_package_coupon: Optional[bool] = None


class CouponResponseCommon(CouponBasePublic):
    id: UUID
    price: float = 0.0
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime
    stock: Optional[int] = None
    is_featured: bool = False
    stock_sold: int = 0
    # Nested relationships (populated from joins)
    category: Optional['CategoryInCoupon'] = None
    countries: List['CountryInCoupon'] = Field(default_factory=list)
    # Multi-currency pricing for frontend
    prices: Dict[str, float] = Field(default_factory=dict, description="Prices in all supported currencies")
    discounts: Dict[str, float] = Field(default_factory=dict, description="Discount amounts in all supported currencies")

    @model_validator(mode='before')
    @classmethod
    def compute_stock_sold(cls, data: Any) -> Any:
        """Set stock_sold to current_uses value and extract multi-currency pricing"""
        if hasattr(data, '__dict__'):
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
            data_dict['stock_sold'] = data_dict.get('current_uses', 0)
            
            # Extract multi-currency pricing from pricing JSON field
            pricing = data_dict.get('pricing', {})
            if pricing and isinstance(pricing, dict):
                prices = {}
                discounts = {}
                for currency, values in pricing.items():
                    if isinstance(values, dict):
                        prices[currency] = values.get('price', 0.0)
                        discounts[currency] = values.get('discount_amount', 0.0)
                data_dict['prices'] = prices
                data_dict['discounts'] = discounts
            else:
                # Fallback to default USD pricing if no pricing JSON
                data_dict['prices'] = {'USD': data_dict.get('price', 0.0)}
                data_dict['discounts'] = {'USD': data_dict.get('discount_amount', 0.0)}
            
            return data_dict
        elif isinstance(data, dict):
            data['stock_sold'] = data.get('current_uses', 0)
            
            # Extract multi-currency pricing from pricing JSON field
            pricing = data.get('pricing', {})
            if pricing and isinstance(pricing, dict):
                prices = {}
                discounts = {}
                for currency, values in pricing.items():
                    if isinstance(values, dict):
                        prices[currency] = values.get('price', 0.0)
                        discounts[currency] = values.get('discount_amount', 0.0)
                data['prices'] = prices
                data['discounts'] = discounts
            else:
                # Fallback to default USD pricing if no pricing JSON
                data['prices'] = {'USD': data.get('price', 0.0)}
                data['discounts'] = {'USD': data.get('discount_amount', 0.0)}
        
        return data

    model_config = ConfigDict(from_attributes=True)


class CouponPublicResponse(CouponResponseCommon):
    """Public response without secret codes"""
    pass


class CouponResponse(CouponResponseCommon):
    """Admin/Full response with codes"""
    code: str
    redeem_code: Optional[str] = None


# Nested schemas for relationships (to avoid circular imports)
class CategoryInCoupon(BaseModel):
    """Simplified category info for nested in coupon responses"""
    id: UUID
    name: str
    slug: str
    
    model_config = ConfigDict(from_attributes=True)


class CountryInCoupon(BaseModel):
    """Simplified country info for nested in coupon responses"""
    id: UUID
    name: str
    slug: str
    country_code: str
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references
# Update forward references
CouponResponse.model_rebuild()
CouponPublicResponse.model_rebuild()


class CouponValidateRequest(BaseModel):
    """Request schema for coupon validation"""
    code: str = Field(..., min_length=1, max_length=50, description="Coupon code to validate")
    purchase_amount: Optional[float] = Field(default=None, ge=0, description="Purchase amount to calculate discount")


class CouponValidateResponse(BaseModel):
    """Response schema for coupon validation"""
    valid: bool
    code: str
    message: str
    discount_type: Optional[str] = None
    discount_amount: Optional[float] = None
    min_purchase: Optional[float] = None
    calculated_discount: Optional[float] = None
    final_amount: Optional[float] = None
