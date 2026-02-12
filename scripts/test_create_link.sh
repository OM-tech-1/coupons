#!/bin/bash

# Configuration
API_KEY="836c816bfd3529cf9efd137f1ba198c07af61e1c08278656777d6a9136651603"
URL="https://api.vouchergalaxy.com/api/v1/external/payment-link"

# Generate a random reference ID
REF_ID="TEST-$(date +%s)"

# Construct Payload (Compact JSON is required for signature matching)
# We use python to ensure correct JSON formatting and signature generation to avoid shell quoting issues
read -r PAYMENT_URL SIGNATURE PAYLOAD <<< $(python3 -c "
import hmac, hashlib, json
payload = {
    'phone_number': '+971501234567',
    'amount': 3.4,
    'currency': 'AED',
    'reference_id': '$REF_ID',
    'return_url': 'https://vouchergalaxy.com/success',
    'webhook_url': 'https://n8n.thegreencertificate.com/webhook/4cc151bc-f040-4d28-adaa-7fec804cde2f'
}
# Compact JSON
body = json.dumps(payload, separators=(',', ':'))
# HMAC Signature
sig = hmac.new('$API_KEY'.encode(), body.encode(), hashlib.sha256).hexdigest()
print(f'Starting... {sig} {body}')
print(f'{body}')
print(f'{sig}')
" | tail -n 2) # Crude way to grab last 2 lines if needed, but let's do it cleaner:

# Re-doing the python part to just print the curl command to be safe and easy
CMD=$(python3 -c "
import hmac, hashlib, json
api_key = '$API_KEY'
url = '$URL'
payload = {
    'phone_number': '+971501234567',
    'amount': 3.4,
    'currency': 'AED',
    'reference_id': '$REF_ID',
    'return_url': 'https://vouchergalaxy.com/success',
    'webhook_url': 'https://n8n.thegreencertificate.com/webhook/4cc151bc-f040-4d28-adaa-7fec804cde2f'
}
body = json.dumps(payload, separators=(',', ':'))
sig = hmac.new(api_key.encode(), body.encode(), hashlib.sha256).hexdigest()

# Escape single quotes for shell
body_escaped = body.replace(\"'\", \"'\\''\")

print(f\"curl -X POST {url} -H 'Content-Type: application/json' -H 'X-Signature: {sig}' -d '{body_escaped}'\")
")

echo "Generated cURL command:"
echo "$CMD"
echo ""
echo "Running..."
eval "$CMD"
