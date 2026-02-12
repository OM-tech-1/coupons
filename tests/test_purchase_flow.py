
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
        o = self.db.query(Order).get(order_id)
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
