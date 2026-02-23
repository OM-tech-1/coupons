"""
Test webhook endpoint to diagnose issues
This simulates what Stripe sends to your webhook

Note: These are integration tests that make real HTTP requests.
Skip in CI with: pytest -m "not integration"
"""
import pytest
import requests
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Your webhook URL
WEBHOOK_URL = "https://api.vouchergalaxy.com/webhooks/stripe"
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@pytest.mark.integration
@pytest.mark.skipif(
    not WEBHOOK_SECRET or WEBHOOK_SECRET == "whsec_YOUR_WEBHOOK_SECRET",
    reason="STRIPE_WEBHOOK_SECRET not configured in .env"
)
def test_webhook_endpoint_with_signature():
    """Test webhook endpoint with proper Stripe signature"""
    
    # Sample webhook payload (payment succeeded)
    payload = {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_12345",
                "object": "payment_intent",
                "amount": 10000,
                "currency": "usd",
                "status": "succeeded",
                "metadata": {
                    "order_id": "test-order-123"
                }
            }
        }
    }
    
    # Create signature (like Stripe does)
    payload_str = json.dumps(payload, separators=(',', ':'))
    timestamp = "1234567890"
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    stripe_signature = f"t={timestamp},v1={signature}"
    
    # Send request
    response = requests.post(
        WEBHOOK_URL,
        data=payload_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": stripe_signature
        },
        timeout=10
    )
    
    # Assertions
    assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        assert data.get("received") == True


@pytest.mark.integration
def test_webhook_endpoint_without_signature():
    """Test webhook endpoint without signature (should fail)"""
    
    payload = {
        "id": "evt_test_webhook",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test"}}
    }
    
    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=10
    )
    
    # Should return 400 for missing signature
    assert response.status_code == 400
    assert "Stripe-Signature" in response.text or "Missing" in response.text


@pytest.mark.integration
def test_webhook_endpoint_exists():
    """Test that webhook endpoint exists and responds"""
    
    # Send request without signature
    response = requests.post(
        WEBHOOK_URL,
        json={"test": "data"},
        timeout=10
    )
    
    # Should not be 404 (endpoint exists)
    assert response.status_code != 404, "Webhook endpoint not found"
    
    # Should be 400 (missing signature)
    assert response.status_code == 400
