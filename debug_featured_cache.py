#!/usr/bin/env python3
"""
Debug featured coupons endpoint - check cache and database
"""
import os
import sys
import json

# Test Redis connection and cache
print("=" * 60)
print("🔍 Testing Redis Cache Layer")
print("=" * 60)
print()

try:
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://:couponRedisServer@193.203.160.61:6379/0")
    print(f"📍 Redis URL: {redis_url}")
    
    client = redis.from_url(redis_url, decode_responses=True)
    client.ping()
    print("✅ Redis connection: OK")
    print()
    
    # Check for cached featured coupons
    cache_key = "coupons:featured:10"
    cached_value = client.get(cache_key)
    
    if cached_value:
        print(f"📦 Cache key '{cache_key}' exists")
        data = json.loads(cached_value)
        print(f"   Cached items: {len(data)}")
        if len(data) > 0:
            print(f"   First item: {data[0].get('code', 'N/A')}")
        else:
            print("   ⚠️  Cache contains empty array!")
    else:
        print(f"❌ Cache key '{cache_key}' not found")
        print("   This means the endpoint hasn't been called yet, or cache expired")
    print()
    
    # Clear the cache to force fresh query
    print("🗑️  Clearing featured coupons cache...")
    deleted = client.delete(cache_key)
    print(f"   Deleted {deleted} key(s)")
    print()
    
except Exception as e:
    print(f"❌ Redis error: {e}")
    print()

# Now check what keys exist in Redis
print("=" * 60)
print("🔍 Checking Redis Keys")
print("=" * 60)
print()

try:
    all_keys = client.keys("coupons:*")
    print(f"📊 Total coupon-related keys: {len(all_keys)}")
    
    if len(all_keys) > 0:
        print("\nSample keys:")
        for key in all_keys[:10]:
            print(f"  - {key}")
    print()
    
except Exception as e:
    print(f"❌ Error listing keys: {e}")
    print()

print("=" * 60)
print("💡 Next Steps:")
print("=" * 60)
print()
print("1. Cache has been cleared")
print("2. Call the API endpoint: GET /coupons/featured?limit=10")
print("3. This will force a fresh database query")
print()
print("If it still returns empty array, the issue is:")
print("  - No coupons have is_featured=true AND is_active=true")
print("  - Database connection issue")
print()
