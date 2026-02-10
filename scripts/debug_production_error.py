
import requests
import hmac
import hashlib
import json
import uuid

BASE_URL = "https://api.vouchergalaxy.com"
EXTERNAL_API_KEY = "836c816bfd3529cf9efd137f1ba198c07af61e1c08278656777d6a9136651603"

def sign_request(payload):
    body = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        EXTERNAL_API_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return body, signature

def main():
    print("Debugging Production Error...")
    
    # Use a reference ID that likely exists or doesn't, we just want to see if it 500s or 404s properly.
    # Actually, let's create a fresh one to be sure we are hitting the code path.
    ref_id = f"REF-DEBUG-{uuid.uuid4().hex[:8]}"
    
    # 1. Create Link (to populate DB)
    create_payload = {
        "phone_number": "+971501234567",
        "amount": 10.0,
        "currency": "AED",
        "reference_id": ref_id,
        "return_url": "https://google.com"
    }
    body, sig = sign_request(create_payload)
    headers = {"Content-Type": "application/json", "X-Signature": sig}
    
    print(f"Creating link for {ref_id}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", data=body, headers=headers, timeout=10)
        print(f"Create Link Status: {resp.status_code}")
        print(f"Create Link Response: {resp.text}")
    except Exception as e:
        print(f"Create Link Exception: {e}")
        return

    # 2. Check Status
    print(f"Checking status for {ref_id}...")
    status_payload = {"reference_id": ref_id}
    body, sig = sign_request(status_payload)
    headers = {"Content-Type": "application/json", "X-Signature": sig}
    
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-status", data=body, headers=headers, timeout=10)
        print(f"Status Check Code: {resp.status_code}")
        print(f"Status Check Response: {resp.text}")
    except Exception as e:
        print(f"Status Check Exception: {e}")

if __name__ == "__main__":
    main()
