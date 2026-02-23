"""
Test webhook endpoint to diagnose issues
This simulates what Stripe sends to your webhook
"""
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

print("="*60)
print("WEBHOOK ENDPOINT TEST")
print("="*60)
print(f"\nWebhook URL: {WEBHOOK_URL}")
print(f"Webhook Secret: {'Set' if WEBHOOK_SECRET else 'NOT SET'}")

if not WEBHOOK_SECRET or WEBHOOK_SECRET == "whsec_YOUR_WEBHOOK_SECRET":
    print("\n❌ ERROR: Webhook secret not configured!")
    print("Cannot test signature verification without real secret.")
    print("\nTo fix:")
    print("1. Get secret from Stripe Dashboard")
    print("2. Update .env file: STRIPE_WEBHOOK_SECRET=whsec_...")
    exit(1)

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

print(f"\nSending test webhook...")
print(f"Event type: {payload['type']}")
print(f"Payment Intent: {payload['data']['object']['id']}")

try:
    response = requests.post(
        WEBHOOK_URL,
        data=payload_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": stripe_signature
        },
        timeout=10
    )
    
    print(f"\n{'='*60}")
    print(f"RESPONSE")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - Webhook received and processed")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
    elif response.status_code == 400:
        print("❌ BAD REQUEST - Signature verification failed or invalid payload")
        print(f"Response: {response.text}")
    elif response.status_code == 404:
        print("❌ NOT FOUND - Webhook endpoint doesn't exist")
        print("Check if your application is deployed")
    elif response.status_code == 500:
        print("❌ SERVER ERROR - Bug in webhook handler")
        print(f"Response: {response.text}")
    else:
        print(f"⚠️  Unexpected status code")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("\n❌ TIMEOUT - Server took too long to respond")
    print("Check if your application is running")
except requests.exceptions.ConnectionError:
    print("\n❌ CONNECTION ERROR - Cannot reach server")
    print("Check if your application is deployed and accessible")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print(f"\n{'='*60}")
