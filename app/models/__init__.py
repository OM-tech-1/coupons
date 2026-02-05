# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.coupon import Coupon
from app.models.user_coupon import UserCoupon
from app.models.cart import Cart
from app.models.order import Order
from app.models.payment import Payment
from app.models.category import Category
from app.models.region import Region
from app.models.country import Country
from app.models.coupon_country import CouponCountry

__all__ = [
    "User",
    "Coupon",
    "UserCoupon",
    "Cart",
    "Order",
    "Payment",
    "Category",
    "Region",
    "Country",
    "CouponCountry",
]
