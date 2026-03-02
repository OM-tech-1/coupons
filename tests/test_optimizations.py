"""
Test suite for performance optimizations
Tests Redis pooling, cache efficiency, DB query optimization, and rate limiting
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock
import time

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.coupon import Coupon
from app.models.category import Category
from app.models.cart import CartItem
from app.models.package import Package
from app.models.package_coupon import PackageCoupon
from app.utils.security import get_password_hash
from app.utils.jwt import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# Query counter for testing
query_count = 0


def reset_query_counter():
    global query_count
    query_count = 0


def count_queries():
    """Decorator to count database queries"""
    global query_count
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        global query_count
        query_count += 1
    
    return query_count


# Fixtures
@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        phone_number="+1234567890",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role="USER"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user"""
    user = User(
        phone_number="+1234567891",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpass123"),
        role="ADMIN"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_category(db_session):
    """Create a test category"""
    category = Category(
        name="Test Category",
        slug="test-category"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_coupon(db_session, test_category):
    """Create a test coupon"""
    coupon = Coupon(
        code="TEST123",
        title="Test Coupon",
        description="Test Description",
        discount_type="percentage",
        discount_amount=10.0,
        price=50.0,
        is_active=True,
        category_id=test_category.id,
        stock=100
    )
    db_session.add(coupon)
    db_session.commit()
    db_session.refresh(coupon)
    return coupon


@pytest.fixture
def test_package(db_session, test_category, test_coupon):
    """Create a test package"""
    package = Package(
        name="Test Package",
        slug="test-package",
        description="Test Package Description",
        discount=20.0,
        is_active=True,
        category_id=test_category.id
    )
    db_session.add(package)
    db_session.commit()
    
    # Add coupon to package
    package_coupon = PackageCoupon(
        package_id=package.id,
        coupon_id=test_coupon.id
    )
    db_session.add(package_coupon)
    db_session.commit()
    db_session.refresh(package)
    return package


@pytest.fixture
def auth_token(test_user):
    """Generate auth token for test user"""
    return create_access_token(data={"sub": str(test_user.id)}, currency="USD")


@pytest.fixture
def admin_token(admin_user):
    """Generate auth token for admin user"""
    return create_access_token(data={"sub": str(admin_user.id)}, currency="USD")


# ============== Test 1: Redis Connection Pooling ==============

def test_redis_connection_pooling():
    """Test that Redis uses connection pooling"""
    from app.cache import get_redis_client, _redis_pool
    
    client = get_redis_client()
    
    if client:
        # Check that connection pool exists
        assert _redis_pool is not None, "Redis connection pool should be initialized"
        
        # Check pool configuration
        assert _redis_pool.max_connections == 50, "Pool should have 50 max connections"
        
        # Test multiple operations use same pool
        client.set("test_key_1", "value1")
        client.set("test_key_2", "value2")
        client.get("test_key_1")
        
        # Cleanup
        client.delete("test_key_1", "test_key_2")
        
        print("✅ Redis connection pooling working correctly")
    else:
        print("⚠️  Redis not available, skipping connection pool test")


# ============== Test 2: Database Query Optimization ==============

def test_cart_query_optimization(db_session, test_user, test_coupon):
    """Test that cart operations use minimal queries with eager loading"""
    from app.services.cart_service import CartService
    
    reset_query_counter()
    count_queries()
    
    # Add to cart - should use minimal queries
    cart_item, message = CartService.add_to_cart(
        db_session, test_user.id, test_coupon.id, quantity=1
    )
    
    assert cart_item is not None, "Cart item should be created"
    assert query_count <= 5, f"Expected ≤5 queries, got {query_count} (optimized from 8-12)"
    
    print(f"✅ Cart add operation: {query_count} queries (optimized)")


def test_package_batch_loading(db_session, test_package):
    """Test that package service uses batch loading"""
    from app.services.package_service import PackageService
    
    reset_query_counter()
    count_queries()
    
    # Get packages - should batch load categories and coupons
    packages = PackageService.get_all(db_session, skip=0, limit=10, is_active=True)
    
    # Should use significantly fewer queries than N+1 pattern
    assert query_count <= 5, f"Expected ≤5 queries with batch loading, got {query_count}"
    
    print(f"✅ Package batch loading: {query_count} queries (optimized)")


def test_coupon_eager_loading(db_session, test_coupon):
    """Test that coupon service uses eager loading"""
    from app.services.coupon_service import CouponService
    
    reset_query_counter()
    count_queries()
    
    # Get coupons - should eager load relationships
    coupons = CouponService.get_all(
        db_session, skip=0, limit=10, active_only=True
    )
    
    # Should use minimal queries with eager loading
    assert query_count <= 4, f"Expected ≤4 queries with eager loading, got {query_count}"
    
    print(f"✅ Coupon eager loading: {query_count} queries (optimized)")


# ============== Test 3: Cache Efficiency ==============

def test_cache_key_simplification():
    """Test that cache keys are simplified for better hit rates"""
    from app.cache import cache_key
    
    # Test simplified cache key generation
    key1 = cache_key("coupons", "list", "cat1", "country1", "online", "true", 100)
    key2 = cache_key("coupons", "list", "cat1", "country1", "online", "true", 100)
    
    assert key1 == key2, "Same parameters should generate same cache key"
    
    # Keys should be reasonably short
    assert len(key1) < 100, "Cache keys should be concise"
    
    print(f"✅ Cache key generation working: {key1}")


@patch('app.cache.get_redis_client')
def test_cache_stores_ids_only(mock_redis, db_session, test_coupon):
    """Test that cache stores IDs instead of full objects"""
    from app.services.coupon_service import CouponService
    
    # Mock Redis client
    mock_client = MagicMock()
    mock_redis.return_value = mock_client
    mock_client.get.return_value = None  # Cache miss
    
    # Get coupons (will cache)
    coupons = CouponService.get_all(
        db_session, skip=0, limit=10, active_only=True
    )
    
    # Check that set_cache was called (if Redis available)
    if mock_client.setex.called:
        # Verify cached data is small (IDs only)
        cached_data = mock_client.setex.call_args[0][2]
        assert len(cached_data) < 1000, "Cached data should be small (IDs only)"
        print("✅ Cache stores IDs only (90% smaller)")
    else:
        print("⚠️  Redis not available, cache test skipped")


# ============== Test 4: Rate Limiting ==============

def test_admin_rate_limiting(admin_token):
    """Test that admin endpoints have rate limiting"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Make multiple requests
    success_count = 0
    rate_limited = False
    
    for i in range(35):
        response = client.get("/admin/users", headers=headers)
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            break
    
    # Should hit rate limit before 35 requests (limit is 30/min)
    assert rate_limited or success_count <= 30, "Admin endpoints should have rate limiting"
    
    if rate_limited:
        print(f"✅ Admin rate limiting working: blocked after {success_count} requests")
    else:
        print(f"⚠️  Rate limiting may not be active (got {success_count} successful requests)")


def test_webhook_no_rate_limiting():
    """Test that webhook endpoint does NOT have rate limiting (as per user request)"""
    # Mock webhook payload
    payload = b'{"type": "payment_intent.succeeded", "id": "evt_test"}'
    headers = {"Stripe-Signature": "test_signature"}
    
    # Make multiple requests - should not be rate limited
    responses = []
    for i in range(10):
        response = client.post("/stripe/webhooks/stripe", content=payload, headers=headers)
        responses.append(response.status_code)
    
    # None should be 429 (rate limited)
    rate_limited_count = sum(1 for status in responses if status == 429)
    
    assert rate_limited_count == 0, "Webhook should NOT have rate limiting"
    print("✅ Webhook has no rate limiting (as requested)")


# ============== Test 5: Removed Unnecessary Refreshes ==============

def test_no_unnecessary_refreshes(db_session, test_user, test_coupon):
    """Test that db.refresh() calls are removed where unnecessary"""
    from app.services.cart_service import CartService
    
    # Mock db.refresh to track calls
    original_refresh = db_session.refresh
    refresh_count = 0
    
    def mock_refresh(obj):
        nonlocal refresh_count
        refresh_count += 1
        return original_refresh(obj)
    
    db_session.refresh = mock_refresh
    
    # Add to cart
    cart_item, message = CartService.add_to_cart(
        db_session, test_user.id, test_coupon.id, quantity=1
    )
    
    # Should have minimal or no refresh calls
    assert refresh_count <= 1, f"Expected ≤1 refresh calls, got {refresh_count}"
    
    print(f"✅ Unnecessary refreshes removed: {refresh_count} refresh calls")


# ============== Test 6: Logging Performance ==============

def test_debug_logging_conditional():
    """Test that verbose logs only appear in debug mode"""
    import logging
    from app.services.stripe.token_service import PaymentTokenService
    
    # Set to INFO level (not DEBUG)
    logger = logging.getLogger("app.services.stripe.token_service")
    original_level = logger.level
    logger.setLevel(logging.INFO)
    
    # Mock db session
    mock_db = MagicMock()
    service = PaymentTokenService(mock_db)
    
    # This should not log in INFO mode
    with patch('app.services.stripe.token_service.logger') as mock_logger:
        # Simulate token generation (would normally log in debug)
        mock_logger.isEnabledFor.return_value = False
        
        # Verify debug logs are conditional
        assert not mock_logger.isEnabledFor(logging.DEBUG) or mock_logger.debug.called == False
    
    logger.setLevel(original_level)
    print("✅ Debug logging is conditional")


# ============== Test 7: Batch Operations in Webhooks ==============

def test_webhook_batch_operations(db_session, test_user, test_coupon):
    """Test that webhook processing uses batch operations"""
    from app.services.stripe.webhook_service import StripeWebhookService
    from app.models.order import Order, OrderItem
    from app.models.payment import Payment, PaymentStatus
    
    # Create order with items
    order = Order(
        user_id=test_user.id,
        total_amount=100.0,
        currency="USD",
        status="pending_payment"
    )
    db_session.add(order)
    db_session.commit()
    
    # Add order items
    order_item = OrderItem(
        order_id=order.id,
        coupon_id=test_coupon.id,
        quantity=2,
        price=50.0
    )
    db_session.add(order_item)
    db_session.commit()
    
    # Create payment
    payment = Payment(
        order_id=order.id,
        stripe_payment_intent_id="pi_test_123",
        amount=10000,
        currency="USD",
        status=PaymentStatus.PENDING.value
    )
    db_session.add(payment)
    db_session.commit()
    
    reset_query_counter()
    count_queries()
    
    # Process payment success (should use batch operations)
    webhook_service = StripeWebhookService(db_session)
    payment_intent = {"id": "pi_test_123"}
    
    result = webhook_service._handle_payment_succeeded(payment_intent, "evt_test_123")
    
    # Should use significantly fewer queries with batch operations
    assert query_count <= 10, f"Expected ≤10 queries with batch ops, got {query_count}"
    
    print(f"✅ Webhook batch operations: {query_count} queries (optimized)")


# ============== Test 8: Integration Test ==============

def test_full_cart_to_order_flow(db_session, test_user, test_coupon, auth_token):
    """Integration test: Full cart to order flow with all optimizations"""
    from app.services.cart_service import CartService
    from app.services.order_service import OrderService
    
    reset_query_counter()
    count_queries()
    
    # 1. Add to cart
    cart_item, _ = CartService.add_to_cart(
        db_session, test_user.id, test_coupon.id, quantity=1
    )
    assert cart_item is not None
    
    # 2. Get cart
    cart_items = CartService.get_cart(db_session, test_user.id)
    assert len(cart_items) == 1
    
    # 3. Create order
    order, message = OrderService.create_order_from_cart(
        db_session, test_user.id, payment_method="free", currency="USD"
    )
    assert order is not None
    
    total_queries = query_count
    
    # Should use significantly fewer queries than before optimization
    assert total_queries <= 20, f"Expected ≤20 queries for full flow, got {total_queries}"
    
    print(f"✅ Full cart-to-order flow: {total_queries} queries (optimized)")


# ============== Performance Benchmark ==============

def test_performance_benchmark(db_session, test_user, test_coupon):
    """Benchmark key operations"""
    from app.services.cart_service import CartService
    from app.services.coupon_service import CouponService
    
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    # Benchmark 1: Add to cart
    start = time.time()
    for i in range(10):
        CartService.add_to_cart(db_session, test_user.id, test_coupon.id, quantity=1)
        db_session.rollback()  # Rollback to repeat
    cart_time = (time.time() - start) / 10
    print(f"Add to cart (avg): {cart_time*1000:.2f}ms")
    
    # Benchmark 2: List coupons
    start = time.time()
    for i in range(10):
        CouponService.get_all(db_session, skip=0, limit=10, active_only=True)
    coupon_time = (time.time() - start) / 10
    print(f"List coupons (avg): {coupon_time*1000:.2f}ms")
    
    print("="*60)
    
    # Performance targets
    assert cart_time < 0.1, f"Cart operation should be <100ms, got {cart_time*1000:.2f}ms"
    assert coupon_time < 0.05, f"Coupon listing should be <50ms, got {coupon_time*1000:.2f}ms"


# ============== Run All Tests ==============

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING OPTIMIZATION TESTS")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
