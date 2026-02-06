
import requests
import os
import uuid
import json
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
API_SECRET = os.getenv("EXTERNAL_API_KEY")

if not API_SECRET:
    print("❌ Error: EXTERNAL_API_KEY not found in .env")
    exit(1)

def test_external_security():
    print(f"🚀 Testing External Payment (HMAC + Webhook)...")
    
    payload = {
        "phone_number": f"+971{uuid.uuid4().int % 1000000000}",
        "amount": 150.00,
        "currency": "USD",
        "first_name": "Webhook",
        "second_name": "Tester",
        "reference_id": f"WEB-{uuid.uuid4().hex[:8]}",
        "webhook_url": "https://webhook.site/test-uuid" 
    }

    # 1. Valid Signature
    print("\n1. Testing Valid Request with Webhook...")
    
    body_json = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(API_SECRET.encode(), body_json.encode(), hashlib.sha256).hexdigest()
    
    headers = {
        "x-signature": signature,
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", data=body_json, headers=headers)
        
        if resp.status_code == 200:
            print("✅ Success!")
            print(f"   URL: {resp.json()['payment_url']}")
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(f"   Response: {resp.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_external_security()
