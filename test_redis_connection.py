#!/usr/bin/env python3
"""
Redis Connection Test - Testing the updated credentials
"""
import redis
import sys

# Get the Redis URL from environment or use the new one
redis_url = "redis://:couponRedisServer@193.203.160.61:6379/0"

print("🔍 Testing Redis connection with updated credentials...")
print(f"📍 Redis URL: {redis_url}")
print(f"📍 Password: couponRedisServer")
print()

try:
    # Create Redis client
    client = redis.from_url(redis_url, decode_responses=True)
    
    # Test 1: Ping
    print("✅ Test 1: PING")
    response = client.ping()
    print(f"   Response: {response}")
    print()
    
    # Test 2: Set a test key
    print("✅ Test 2: SET test_key")
    client.set("test_connection_key", "Hello from Python!", ex=10)
    print("   Key set successfully (expires in 10s)")
    print()
    
    # Test 3: Get the test key
    print("✅ Test 3: GET test_key")
    value = client.get("test_connection_key")
    print(f"   Value: {value}")
    print()
    
    # Test 4: Get server info
    print("✅ Test 4: Server Info")
    info = client.info("server")
    print(f"   Redis Version: {info.get('redis_version')}")
    print(f"   OS: {info.get('os')}")
    print(f"   Uptime (days): {info.get('uptime_in_days')}")
    print()
    
    # Test 5: Check database size
    print("✅ Test 5: Database Stats")
    dbsize = client.dbsize()
    print(f"   Total keys in DB: {dbsize}")
    print()
    
    # Test 6: Test Redis operations used by the app
    print("✅ Test 6: App-specific operations")
    
    # Test sorted set (for trending)
    client.zadd("test:trending", {"coupon1": 10, "coupon2": 20})
    trending = client.zrevrange("test:trending", 0, 1, withscores=True)
    print(f"   Sorted set (trending): {trending}")
    
    # Test list (for recently viewed)
    client.lpush("test:recent", "item1", "item2")
    recent = client.lrange("test:recent", 0, 1)
    print(f"   List (recent): {recent}")
    
    # Test hash (for stock)
    client.hset("test:stock", "coupon1", "100")
    stock = client.hget("test:stock", "coupon1")
    print(f"   Hash (stock): {stock}")
    print()
    
    # Cleanup
    client.delete("test_connection_key", "test:trending", "test:recent", "test:stock")
    
    print("=" * 60)
    print("🎉 All tests passed! Redis is working perfectly!")
    print("=" * 60)
    print()
    print("✅ Your application can now use Redis for:")
    print("   - Trending coupons")
    print("   - Recently viewed items")
    print("   - Real-time stock tracking")
    print("   - Caching")
    
except redis.ConnectionError as e:
    print("❌ Connection Error!")
    print(f"   Error: {e}")
    sys.exit(1)
    
except redis.AuthenticationError as e:
    print("❌ Authentication Error!")
    print(f"   Error: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
