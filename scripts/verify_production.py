import requests
import sys
import time
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

def check_endpoint(method, path, name):
    url = f"{BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=10)
        status = response.status_code
        print(f"[{status}] {name}: {url}")
        return status in [200, 201, 400, 401, 403, 405, 422]
    except Exception as e:
        print(f"!!! Error hitting {name}: {e}")
        return False

def verify_external_flow():
    print("\n🔐 Verifying External Payment Status Flow...")
    
    # 1. Create a Payment Link
    ref_id = f"REF-PROD-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "phone_number": "+971501234567",
        "amount": 10.0,
        "currency": "AED",
        "reference_id": ref_id,
        "return_url": "https://google.com"
    }
    
    body, sig = sign_request(create_payload)
    headers = {"Content-Type": "application/json", "X-Signature": sig}
    
    print(f"   -> Creating Link for Reference: {ref_id}")
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-link", data=body, headers=headers)
        if resp.status_code != 200:
            print(f"   ❌ Failed to create link: {resp.status_code} - {resp.text}")
            return False
        print("   ✅ Link Created Successfully.")
    except Exception as e:
        print(f"   ❌ Exception creating link: {e}")
        return False
        
    # 2. Check Status
    print(f"   -> Checking Status for Reference: {ref_id}")
    status_payload = {"reference_id": ref_id}
    body, sig = sign_request(status_payload)
    headers = {"Content-Type": "application/json", "X-Signature": sig}
    
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-status", data=body, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data['reference_id'] == ref_id and data['status'] == 'initiated':
                 print(f"   ✅ Status Check Passed: {data}")
                 return True
            else:
                 print(f"   ⚠️ Status Check Mismatch: {data}")
                 return False
        elif resp.status_code == 404:
            print(f"   ❌ Endpoint verified as NOT deployed (404 Not Found)")
            return False
        else:
            print(f"   ❌ Status Check Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception checking status: {e}")
        return False

def main():
    print(f"Starting Production Verification against {BASE_URL}")
    
    # 1. Health Check
    if not check_endpoint("GET", "/health", "Health Check"):
        print("Health check failed! Aborting.")
        sys.exit(1)
        
    # 2. Key Endpoints Coverage
    endpoints = [
        ("GET", "/coupons/", "List Coupons"),
        ("GET", "/categories/", "List Categories"),
        ("GET", "/regions/", "List Regions"),
        ("GET", "/countries/", "List Countries"),
    ]
    
    for method, path, name in endpoints:
        check_endpoint(method, path, name)
            
    # 3. Verify New Feature Flow
    if verify_external_flow():
        print("\n✅ Production Verification Passed! New Endpoint is LIVE.")
    else:
        print("\n❌ Verification Failed. Deployment might be pending or failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
