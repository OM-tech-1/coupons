import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import engine, Base
# Import all models to ensure they are registered
from app.models import (
    User, Coupon, UserCoupon, CartItem, Order, Payment, PaymentToken,
    Category, Region, Country, CouponCountry, Package, PackageCoupon
)
from app.models.contact_message import ContactMessage

def init_database():
    print("✨ Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    init_database()
