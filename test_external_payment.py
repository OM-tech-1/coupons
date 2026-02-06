
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

def sign_payload(secret, payload_dict):
    body_str = json.dumps(payload_dict, separators=(',', ':')) # Pydantic/FastAPI might tolerate spaces but standard JSON match is key. 
    # NOTE: requests json= argument produces compact json by default? No, it uses spacers.
    # To match exactly what 'requests' sends, we should serialize it manually and send as data.
    return hmac.new(secret.encode(), body_str.encode(), hashlib.sha256).hexdigest(), body_str

def test_external_security():
    print(f"🚀 Testing External Payment Security (HMAC)...")
    
    payload = {
        "phone_number": f"+971{uuid.uuid4().int % 1000000000}",
        "amount": 150.00,
        "currency": "USD",
        "first_name": "Secure",
        "second_name": "User",
        "reference_id": f"SEC-{uuid.uuid4().hex[:8]}"
    }

    # 1. Valid Signature
    print("\n1. Testing Valid Signature...")
    
    # We must manually dump to ensure byte-for-byte match with signature
    body_json = json.dumps(payload) 
    # Important: requests `json=payload` might serialize differently (spaces). 
    # Let's verify what requests does. Usually `{"key": "value"}` with space.
    # To be safe, we generate signature on the EXACT string we send.
    
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

    # 2. Tampered Payload (Sig Mismatch)
    print("\n2. Testing Tampered Payload...")
    tampered_body = body_json.replace("150.0", "1.0") # Hacker tries to pay less
    # Sending tampered body but ORIGINAL signature
    resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", data=tampered_body, headers=headers)
    
    if resp.status_code == 401:
        print("✅ Correctly rejected (401)")
    else:
        print(f"❌ Expected 401, got {resp.status_code}")

if __name__ == "__main__":
    test_external_security()
