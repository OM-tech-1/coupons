import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import engine, Base
# Import all models to ensure they are registered
from app.models import (
    User, Coupon, UserCoupon, CartItem, Order, Payment, PaymentToken,
    Category, Region, Country, CouponCountry
)

def reset_database():
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Operation cancelled.")
        return

    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("✨ Recreating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset successfully!")

if __name__ == "__main__":
    reset_database()
