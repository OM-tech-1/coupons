
import pytest
from app.api.external import payment
import json
import hmac
import hashlib

def test_external_payment_status_flow(client, monkeypatch, db):
    """Test creating a payment link and then checking its status"""
    
    # 1. Setup Mocking
    secret = "test-status-secret"
    monkeypatch.setattr(payment, "EXTERNAL_API_SECRET", secret)
    
    # Mock Stripe Service to avoid actual Stripe calls during link creation
    from app.services.stripe.payment_service import StripePaymentService
    from app.models.order import Order
    from types import SimpleNamespace
    
    def mock_create_intent(self, order_id, amount, currency, metadata):
        from app.models.payment import Payment, PaymentStatus, PaymentGateway
        
        o = self.db.get(Order, order_id)
        if o:
            o.stripe_payment_intent_id = "pi_status_test_123"
            
        # Create Payment Record (Crucial for status check!)
        payment = Payment(
            order_id=order_id,
            stripe_payment_intent_id="pi_status_test_123",
            stripe_client_secret="sk_test_mock",
            amount=amount,
            currency=currency,
            status=PaymentStatus.INITIATED.value,
            gateway=PaymentGateway.STRIPE.value,
            payment_metadata=metadata  # This contains the reference_id!
        )
        self.db.add(payment)
        self.db.commit()
        
        return SimpleNamespace(stripe_payment_intent_id="pi_status_test_123")
    
    monkeypatch.setattr(StripePaymentService, "create_payment_intent", mock_create_intent)

    # 2. Create Payment Link (to populate DB)
    ref_id = "REF_STATUS_CHECK_001"
    create_payload = {
        "phone_number": "+1234567890",
        "amount": 50.0,
        "currency": "USD",
        "reference_id": ref_id
    }
    create_body = json.dumps(create_payload, separators=(',', ':'))
    create_sig = hmac.new(secret.encode(), create_body.encode(), hashlib.sha256).hexdigest()
    
    resp = client.post(
        "/api/v1/external/payment-link",
        data=create_body,
        headers={"Content-Type": "application/json", "X-Signature": create_sig}
    )
    assert resp.status_code == 200
    
    # 3. Check Status
    status_payload = {"reference_id": ref_id}
    status_body = json.dumps(status_payload, separators=(',', ':'))
    status_sig = hmac.new(secret.encode(), status_body.encode(), hashlib.sha256).hexdigest()
    
    resp = client.post(
        "/api/v1/external/payment-status",
        data=status_body,
        headers={"Content-Type": "application/json", "X-Signature": status_sig}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["reference_id"] == ref_id
    assert data["status"] == "pending"  # Mapped from initiated
    assert float(data["amount"]) == 50.0
    assert data["currency"] == "USD"
    assert "created_at" in data
    assert "order_id" in data

def test_external_payment_status_not_found(client, monkeypatch):
    """Test checking status for non-existent reference"""
    secret = "test-status-secret"
    monkeypatch.setattr(payment, "EXTERNAL_API_SECRET", secret)
    
    ref_id = "NON_EXISTENT_REF"
    payload = {"reference_id": ref_id}
    body = json.dumps(payload, separators=(',', ':'))
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    
    resp = client.post(
        "/api/v1/external/payment-status",
        data=body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    
    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Payment with reference_id {ref_id} not found"

def test_external_payment_status_success_mapping(client, monkeypatch, db):
    """Test that 'succeeded' internal status maps to 'success'"""
    
    # 1. Setup Mocking
    from app.api.external import payment
    monkeypatch.setattr(payment, "EXTERNAL_API_SECRET", "test-secret")
    
    # 2. Directly create a successful payment in DB
    from app.models.payment import Payment, PaymentStatus
    from app.models.order import Order
    from app.models.user import User
    import uuid
    
    # Create User first
    user = User(
        phone_number="+100000000",
        hashed_password="hashed_secret",
        full_name="Test User",
        role="USER"
    )
    db.add(user)
    db.commit()
    
    ref_id = "REF_SUCCESS_001"
    order = Order(
        user_id=user.id,
        total_amount=100.0,
        status="paid",
        reference_id=ref_id
    )
    db.add(order)
    db.commit()
    
    ref_id = "REF_SUCCESS_001"
    payment_obj = Payment(
        order_id=order.id,
        amount=10000, # cents
        currency="USD",
        status=PaymentStatus.SUCCEEDED.value,
        payment_metadata={"reference_id": ref_id}
    )
    db.add(payment_obj)
    db.commit()
    
    # 3. Check status via API
    import json
    import hmac
    import hashlib
    
    payload = {"reference_id": ref_id}
    body = json.dumps(payload, separators=(',', ':'))
    sig = hmac.new(b"test-secret", body.encode(), hashlib.sha256).hexdigest()
    
    resp = client.post(
        "/api/v1/external/payment-status",
        data=body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
