import requests
import hmac
import hashlib
import json
import os
import sys
import time

# Configuration
API_BASE = "https://api.vouchergalaxy.com"
EXTERNAL_KEY = "836c816bfd3529cf9efd137f1ba198c07af61e1c08278656777d6a9136651603" # From .env

def test_production_deployment():
    print(f"📡 Testing {API_BASE}...")
    
    # 1. Generate Payment Link
    link_url = f"{API_BASE}/api/v1/external/payment-link"
    payload = {
        "phone_number": "+971501234567",
        "amount": 5.00,
        "currency": "AED",
        "reference_id": "PROD-TEST-REDIRECTION",
        "return_url": "https://verification.com/success"  # This is what we check for
    }
    
    body = json.dumps(payload)
    signature = hmac.new(
        EXTERNAL_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print("1️⃣  Generating Payment Link...")
    try:
        resp = requests.post(link_url, data=body, headers={
            "Content-Type": "application/json",
            "X-Signature": signature
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        payment_url = data['payment_url']
        print(f"   ✅ Link generated: {payment_url}")
        
        # Extract Token
        # format: https://.../pay?token=XYZ...
        token = payment_url.split("token=")[1].split("&")[0]
        
    except Exception as e:
        print(f"   ❌ Failed to generate link: {e}")
        print(f"   Response: {resp.text if 'resp' in locals() else 'N/A'}")
        return

    # 2. Validate Token (Check for return_url)
    validate_url = f"{API_BASE}/payments/validate-token"
    print("\n2️⃣  Validating Token to check for 'return_url'...")
    
    try:
        resp = requests.post(validate_url, json={"token": token}, timeout=10)
        resp.raise_for_status()
        val_data = resp.json()
        
        actual_return_url = val_data.get('return_url')
        print(f"   🔍 URL in response: {actual_return_url}")
        
        if actual_return_url == payload['return_url']:
            print("\n🎉 SUCCESS: Production is updated! 'return_url' is present.")
        else:
            print("\n⚠️  FAILURE: 'return_url' is missing or incorrect.")
            print("   The deployment might still be in progress. Please wait a few minutes and try again.")
            
    except Exception as e:
        print(f"   ❌ Failed to validate token: {e}")
        print(f"   Response: {resp.text if 'resp' in locals() else 'N/A'}")

if __name__ == "__main__":
    test_production_deployment()
