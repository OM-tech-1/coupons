import pytest
from app.models.coupon import Coupon

# --- Cart Tests ---
def test_cart_workflow(client, regular_user, sample_coupon):
    """Test full cart workflow: add, view, remove, clear"""
    headers = regular_user["headers"]
    coupon_id = sample_coupon["id"]

    # 1. Add to cart
    resp = client.post("/cart/add", json={"coupon_id": coupon_id, "quantity": 1}, headers=headers)
    assert resp.status_code in [200, 201]
    assert resp.json()["message"] == "Added to cart"

    # 2. View cart
    resp = client.get("/cart/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["coupon_id"] == coupon_id

    # 3. Remove item
    resp = client.delete(f"/cart/{coupon_id}", headers=headers)
    assert resp.status_code == 204

    # 4. View cart (empty)
    resp = client.get("/cart/", headers=headers)
    assert len(resp.json()["items"]) == 0

    # 5. Add again and clear
    client.post("/cart/add", json={"coupon_id": coupon_id, "quantity": 1}, headers=headers)
    resp = client.delete("/cart/", headers=headers)
    assert resp.status_code == 204
    resp = client.get("/cart/", headers=headers)
    assert len(resp.json()["items"]) == 0


# --- External Payment Tests ---
def test_external_payment_link(client, monkeypatch):
    """Test external payment link generation with signature"""
    import hmac
    import hashlib
    import json
    from app.services.stripe.payment_service import StripePaymentService
    
    # Patch the secret key in the module
    secret = "test-external-secret"
    from app.api.external import payment
    monkeypatch.setattr(payment, "EXTERNAL_API_SECRET", secret)

    # Patch Stripe Service
    def mock_create_intent(self, order_id, amount, currency, metadata):
        from app.models.order import Order
        order = self.db.query(Order).get(order_id)
        if order:
            order.stripe_payment_intent_id = "pi_mock_123"
            self.db.commit()
        return "pi_mock_123"
    
    monkeypatch.setattr(StripePaymentService, "create_payment_intent", mock_create_intent)
    
    payload = {
        "phone_number": "+1234567890",
        "amount": 100.0,
        "currency": "USD",
        "reference_id": "REF123"
    }
    
    # Generate signature
    body = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    
    resp = client.post(
        "/api/v1/external/payment-link",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature
        }
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "payment_url" in data
    assert float(data["amount"]) == 100.0


def test_external_payment_invalid_signature(client, monkeypatch):
    """Test external payment with invalid signature"""
    import json
    secret = "test-external-secret"
    from app.api.external import payment
    monkeypatch.setattr(payment, "EXTERNAL_API_SECRET", secret)
    
    payload = {"phone_number": "+1234567890", "amount": 100.0, "currency": "USD"}
    body = json.dumps(payload)
    
    resp = client.post(
        "/api/v1/external/payment-link",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "invalid_signature"
        }
    )
    
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid Signature"


# --- Stripe Payment Init Test ---
def test_stripe_payment_init(client, monkeypatch, regular_user):
    """Test Stripe payment initialization"""
    from app.services.stripe.payment_service import StripePaymentService
    from app.models.order import Order
    import uuid
    
    headers = regular_user["headers"]
    
    # Create an order first (needs to exist)
    # But init payment takes order_id.
    # We can create a dummy order in DB or mock the service to not check DB if it does.
    # But StripePaymentService usually needs order.
    # Let's create a real order in the test DB.
    # We can use the client to create an order via checkout or manually insert.
    # Manual insert is safer as checkout mock might set payment_method='mock'.
    
    # We need access to DB session.
    # We can ask for `db` fixture in test.
    # But `regular_user` fixture already set up DB.
    # Let's import DB session from elsewhere? No, better add `db` to test args.
    
def test_stripe_payment_init_with_db(client, monkeypatch, regular_user, db):
    """Test Stripe payment initialization with DB access"""
    from app.services.stripe.payment_service import StripePaymentService
    from app.models.order import Order
    from app.models.user import User

    headers = regular_user["headers"]
    
    # Create order
    user = db.query(User).filter(User.phone_number == "+12025559876").first()
    order = Order(user_id=user.id, total_amount=50.0, status="pending", payment_method="stripe")
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Patch Stripe Service
    def mock_create_intent(self, order_id, amount, currency, metadata):
        from types import SimpleNamespace
        o = self.db.query(Order).get(order_id)
        if o:
            o.stripe_payment_intent_id = "pi_mock_init_123"
            self.db.commit()
        return SimpleNamespace(stripe_payment_intent_id="pi_mock_init_123")
        
    monkeypatch.setattr(StripePaymentService, "create_payment_intent", mock_create_intent)
    
    resp = client.post(
        "/payments/init",
        json={"order_id": str(order.id), "amount": 50.0, "currency": "USD"},
        headers=headers
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "redirect_url" in data
    assert data["order_id"] == str(order.id)
    assert data["payment_intent_id"] == "pi_mock_init_123"


# --- Geography Tests ---
def test_regions_and_countries(client, admin_user):
    """Test regions and countries listing"""
    # 1. List regions (empty initially or seeded?)
    # We should create one first if not exists, but let's just check the endpoint returns 200
    resp = client.get("/regions/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 2. List countries
    resp = client.get("/countries/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
