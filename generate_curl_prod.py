import hmac
import hashlib
import json

API_KEY = "836c816bfd3529cf9efd137f1ba198c07af61e1c08278656777d6a9136651603"
URL = "https://api.vouchergalaxy.com/api/v1/external/payment-link"

payload = {
    "phone_number": "+971501234567",
    "amount": 100.00,
    "currency": "AED",
    "reference_id": "DEMO-LINK-001",
    "return_url": "https://google.com",
    "webhook_url": "https://webhook.site/YOUR-UUID"
}

# Important: Separators needed for tight JSON packing if backend expects it, 
# though standard json.dumps usually has spaces. 
# Verification script used default json.dumps?
# Let's check verify_prod_redirection.py... it used `json.dumps(payload)`.
# Standard json.dumps adds spaces: `", "` and `": "`.
# If the backend is strict/FastAPI, it usually parses the body same as sent.
# But HMAC signature verification must utilize the EXACT byte string sent in the body.
# So I will generate the body string first, verify it, and then print it.

body = json.dumps(payload) # Default formatting used in verification script
signature = hmac.new(API_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()

print(f"curl -X POST {URL} \\")
print(f"  -H 'Content-Type: application/json' \\")
print(f"  -H 'X-Signature: {signature}' \\")
print(f"  -d '{body}'")
