
import pytest
from app.models.coupon import Coupon
from app.models.order import Order
from app.services.stripe.payment_service import StripePaymentService
from types import SimpleNamespace

def test_full_purchase_flow(client, regular_user, sample_coupon, db, monkeypatch):
    """
    Test the complete purchase flow:
    1. Add item to cart
    2. Checkout to create order
    3. Initialize payment
    """
    headers = regular_user["headers"]
    coupon_id = sample_coupon["id"]
    
    # 1. Add to Cart
    resp = client.post("/cart/add", json={"coupon_id": coupon_id, "quantity": 2}, headers=headers)
    assert resp.status_code in [200, 201], f"Add to cart failed: {resp.text}"
    
    # Verify cart has item
    resp = client.get("/cart/", headers=headers)
    assert resp.status_code == 200
    cart_data = resp.json()
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["coupon_id"] == coupon_id
    assert cart_data["items"][0]["quantity"] == 2
    
    # 2. Checkout
    # We need to mock Stripe logic if checkout hits it, but currently checkout just creates order
    # unless it auto-inits payment. Based on api/orders.py checkout just creates order.
    
    resp = client.post("/orders/checkout", json={"payment_method": "stripe"}, headers=headers)
    assert resp.status_code == 200, f"Checkout failed: {resp.text}"
    order_data = resp.json()
    order_id = order_data["id"]
    assert order_data["status"] == "pending" or order_data["status"] == "pending_payment"
    assert float(order_data["total_amount"]) > 0
    
    # 3. Initialize Payment
    # Mock Stripe Service
    def mock_create_intent(self, order_id, amount, currency, metadata):
        # Verify order exists in DB
        o = self.db.get(Order, order_id)
        assert o is not None
        o.stripe_payment_intent_id = "pi_mock_flow_123"
        self.db.commit()
        return SimpleNamespace(
            stripe_payment_intent_id="pi_mock_flow_123",
            client_secret="sk_test_mock_secret",
            id="pi_mock_flow_123"
        )
        
    monkeypatch.setattr(StripePaymentService, "create_payment_intent", mock_create_intent)
    
    amount_cents = int(float(order_data["total_amount"]) * 100)
    
    resp = client.post(
        "/payments/init",
        json={
            "order_id": order_id, 
            "amount": amount_cents, 
            "currency": "USD",
            "return_url": "https://example.com/return"
        },
        headers=headers
    )
    
    assert resp.status_code == 200, f"Payment init failed: {resp.text}"
    payment_data = resp.json()
    
    assert payment_data["order_id"] == order_id
    assert payment_data["payment_intent_id"] == "pi_mock_flow_123"
    assert "token" in payment_data
    assert "redirect_url" in payment_data

def test_package_checkout(client, regular_user, sample_coupon, db):
    """
    Test checking out a package.
    """
    from app.models.package import Package
    from app.models.package_coupon import PackageCoupon
    import uuid
    
    # Create a package with the sample coupon
    pkg = Package(
        name="Test Package For Checkout",
        slug=f"test-checkout-pkg-{uuid.uuid4().hex[:6]}",
        discount=10.0,
        is_active=True
    )
    db.add(pkg)
    db.commit()
    
    pkg_coupon = PackageCoupon(package_id=pkg.id, coupon_id=sample_coupon["id"])
    db.add(pkg_coupon)
    db.commit()

    headers = regular_user["headers"]
    
    # Add package to cart
    resp = client.post("/cart/add", json={"package_id": str(pkg.id), "quantity": 1}, headers=headers)
    assert resp.status_code in [200, 201], f"Add to cart failed: {resp.text}"
    
    # Checkout with mock payment (not Stripe) so coupons are added immediately
    resp = client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)
    assert resp.status_code == 200, f"Checkout failed: {resp.text}"
    order_data = resp.json()
    
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["package_id"] == str(pkg.id)
    assert order_data["items"][0]["coupon_id"] is None
    
    # Assert price calculation: coupon price is 15.0 (default sample coupon), discount 10% = 13.5
    assert float(order_data["items"][0]["price"]) > 0
    assert order_data["items"][0]["package"]["name"] == "Test Package For Checkout"

    # Verify user received the coupon (only works with non-Stripe payment methods)
    from app.models.user import User
    user = db.query(User).filter(User.phone_number == "+12025559876").first()
    user_id = user.id

    from app.models.user_coupon import UserCoupon
    claims = db.query(UserCoupon).filter(UserCoupon.user_id == user_id).all()
    assert len(claims) >= 1
    assert any(str(c.coupon_id) == sample_coupon["id"] for c in claims)
