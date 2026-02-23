from pydantic import BaseModel, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID


class CartItemCreate(BaseModel):
    package_id: Optional[UUID] = None
    coupon_id: Optional[UUID] = None
    quantity: int = 1

    @model_validator(mode='after')
    def check_ids(self):
        if not self.package_id and not self.coupon_id:
            raise ValueError('Either package_id or coupon_id must be provided')
        if self.package_id and self.coupon_id:
            raise ValueError('Provide either package_id or coupon_id, not both')
        if self.quantity < 1:
            raise ValueError('Quantity must be at least 1')
        return self


class CouponInCart(BaseModel):
    id: UUID
    code: str
    title: str
    price: float
    discount_amount: float
    currency: str = "USD"
    currency_symbol: str = "$"
    pricing: Optional[Dict[str, Dict[str, float]]] = None
    # Multi-currency pricing for frontend
    prices: Dict[str, float] = {}
    discounts: Dict[str, float] = {}

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to extract multi-currency pricing"""
        data = {
            'id': obj.id,
            'code': obj.code,
            'title': obj.title,
            'price': obj.price,
            'discount_amount': obj.discount_amount,
            'currency': getattr(obj, 'currency', 'USD'),
            'currency_symbol': getattr(obj, 'currency_symbol', '$'),
            'pricing': obj.pricing if hasattr(obj, 'pricing') else None,
        }
        
        # Extract multi-currency pricing
        if hasattr(obj, 'pricing') and obj.pricing and isinstance(obj.pricing, dict):
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


class PackageInCart(BaseModel):
    id: UUID
    name: str
    slug: str
    discount: Optional[float] = None
    picture_url: Optional[str] = None
    price: Optional[float] = None
    pricing: Optional[Dict[str, Dict[str, float]]] = None
    total_price: Optional[Dict[str, float]] = None
    # Multi-currency pricing for frontend
    prices: Dict[str, float] = {}
    final_prices: Dict[str, float] = {}

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to extract multi-currency pricing"""
        data = {
            'id': obj.id,
            'name': obj.name,
            'slug': obj.slug,
            'discount': obj.discount,
            'picture_url': obj.picture_url,
            'price': obj.price,
            'pricing': obj.pricing if hasattr(obj, 'pricing') else None,
            'total_price': obj.total_price if hasattr(obj, 'total_price') else None,
        }
        
        # Extract multi-currency pricing
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
        else:
            # Fallback to single price field
            prices = {'USD': obj.price or 0.0}
            final_prices = {'USD': obj.price or 0.0}
        
        data['prices'] = prices
        data['final_prices'] = final_prices
        
        return cls(**data)

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: UUID
    coupon_id: Optional[UUID] = None
    package_id: Optional[UUID] = None
    quantity: int
    added_at: datetime
    coupon: Optional[CouponInCart] = None
    package: Optional[PackageInCart] = None
    # Multi-currency pricing for this cart item (quantity * unit price)
    prices: Dict[str, float] = {}
    final_prices: Dict[str, float] = {}

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to compute item total with quantity"""
        # Convert nested objects
        coupon = CouponInCart.from_orm(obj.coupon) if obj.coupon else None
        package = PackageInCart.from_orm(obj.package) if obj.package else None
        
        data = {
            'id': obj.id,
            'coupon_id': obj.coupon_id,
            'package_id': obj.package_id,
            'quantity': obj.quantity,
            'added_at': obj.added_at,
            'coupon': coupon,
            'package': package,
        }
        
        # Calculate item total (unit price * quantity)
        prices = {}
        final_prices = {}
        
        if coupon:
            for currency, price in coupon.prices.items():
                prices[currency] = price * obj.quantity
                final_prices[currency] = price * obj.quantity
        elif package:
            for currency, price in package.prices.items():
                prices[currency] = price * obj.quantity
            for currency, final_price in package.final_prices.items():
                final_prices[currency] = final_price * obj.quantity
        
        data['prices'] = prices
        data['final_prices'] = final_prices
        
        return cls(**data)

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: float
    # Multi-currency totals (sum of all items)
    prices: Dict[str, float] = {}
    final_prices: Dict[str, float] = {}

    @classmethod
    def create(cls, items: List[CartItemResponse], total_items: int, total_amount: float):
        """Factory method to compute cart totals"""
        # Sum up prices from all items
        prices = {}
        final_prices = {}
        
        for item in items:
            for currency, price in item.prices.items():
                prices[currency] = prices.get(currency, 0.0) + price
            for currency, final_price in item.final_prices.items():
                final_prices[currency] = final_prices.get(currency, 0.0) + final_price
        
        return cls(
            items=items,
            total_items=total_items,
            total_amount=total_amount,
            prices=prices,
            final_prices=final_prices
        )
