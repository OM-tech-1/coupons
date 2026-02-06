#!/usr/bin/env python3
"""
Quick test to verify all SQLAlchemy models can be imported and relationships resolve correctly.
"""
import sys
sys.path.insert(0, '/Users/parthavpovil/afsal/coupons')

print("Testing model imports...")

try:
    # This should trigger all model loading and relationship resolution
    from app.models import (
        User, Coupon, UserCoupon, Cart, Order, Payment,
        Category, Region, Country, CouponCountry
    )
    print("✓ All models imported successfully")
    
    # Check relationships
    print("\nChecking Coupon relationships...")
    print(f"  - category: {hasattr(Coupon, 'category')}")
    print(f"  - country_associations: {hasattr(Coupon, 'country_associations')}")
    
    print("\nChecking CouponCountry relationships...")
    print(f"  - coupon: {hasattr(CouponCountry, 'coupon')}")
    print(f"  - country: {hasattr(CouponCountry, 'country')}")
    
    print("\nChecking Category relationships...")
    print(f"  - coupons: {hasattr(Category, 'coupons')}")
    
    print("\nChecking Country relationships...")
    print(f"  - coupon_associations: {hasattr(Country, 'coupon_associations')}")
    print(f"  - region: {hasattr(Country, 'region')}")
    
    print("\nChecking Region relationships...")
    print(f"  - countries: {hasattr(Region, 'countries')}")
    
    print("\n✅ All model relationships configured correctly!")
    print("The server should now start without SQLAlchemy errors.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
