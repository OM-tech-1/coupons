
import requests
import os
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("EXTERNAL_API_KEY")

if not API_KEY:
    print("❌ Error: EXTERNAL_API_KEY not found in .env")
    exit(1)

def test_external_payment():
    print(f"🚀 Testing External Payment API...")
    
    # 1. Valid Request (Guest User payment)
    payload = {
        "phone_number": f"+971{uuid.uuid4().int % 1000000000}", # Random phone
        "amount": 299.99,
        "currency": "USD",
        "first_name": "Shadow",
        "second_name": "Tester",
        "reference_id": f"EXT-{uuid.uuid4().hex[:8]}",
        "return_url": "https://google.com"
    }
    
    headers = {"x-api-key": API_KEY}
    
    print("\n1. Testing Valid Request (New User)...")
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", json=payload, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Success!")
            print(f"   Payment URL: {data['payment_url']}")
            print(f"   Order ID: {data['order_id']}")
            print(f"   Status: {data['user_status']}")
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(f"   Response: {resp.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    # 2. Invalid API Key
    print("\n2. Testing Invalid API Key...")
    headers["x-api-key"] = "wrong-key"
    resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", json=payload, headers=headers)
    if resp.status_code == 401:
         print("✅ Correctly rejected (401)")
    else:
         print(f"❌ Expected 401, got {resp.status_code}")

if __name__ == "__main__":
    test_external_payment()
