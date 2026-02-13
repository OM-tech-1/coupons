#!/usr/bin/env python3
"""
Test the featured coupons endpoint
"""
import requests
import json

# You'll need to update this with your actual base URL
base_url = "http://localhost:8000"  # or your production URL

print("🔍 Testing Featured Coupons Endpoint")
print("=" * 60)
print()

try:
    # Test the featured endpoint
    url = f"{base_url}/coupons/featured?limit=10"
    print(f"📍 Calling: {url}")
    
    response = requests.get(url)
    
    print(f"📊 Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data)} featured coupons")
        print()
        
        if len(data) > 0:
            print("📋 Featured Coupons:")
            for coupon in data:
                print(f"  - {coupon.get('code')}: {coupon.get('title')}")
                print(f"    Price: ${coupon.get('price')}, Active: {coupon.get('is_active')}")
                print()
        else:
            print("⚠️  Still returning empty array!")
            print("   Possible reasons:")
            print("   1. Cache hasn't been cleared (wait 5 minutes)")
            print("   2. Server needs restart")
            print("   3. Database connection issue")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Connection Error!")
    print("   Is the server running?")
    print()
    print("💡 Start the server with:")
    print("   uvicorn app.main:app --reload")
    
except Exception as e:
    print(f"❌ Error: {e}")
