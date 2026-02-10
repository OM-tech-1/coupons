
import requests
import hmac
import hashlib
import json
import uuid

BASE_URL = "https://api.vouchergalaxy.com"
EXTERNAL_API_KEY = "836c816bfd3529cf9efd137f1ba198c07af61e1c08278656777d6a9136651603"
REF_ID = "4429eaf5-46be-4c9a-b58a-98d0bcb4903f"

def sign_request(payload):
    body = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        EXTERNAL_API_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return body, signature

def main():
    print(f"Checking status for manually provided Ref ID: {REF_ID}...")
    
    status_payload = {"reference_id": REF_ID}
    body, sig = sign_request(status_payload)
    headers = {"Content-Type": "application/json", "X-Signature": sig}
    
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/external/payment-status", data=body, headers=headers, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("✅ SUCCESS: Status retrieved.")
        else:
            print("❌ FAILURE: Could not retrieve status.")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
