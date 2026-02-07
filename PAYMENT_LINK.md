# Payment Integration Guide

This guide details how to integrate the Secure Payment Link API. This API allows you to generate payment links for your customers programmatically.

## 1. API Endpoint

**URL:** `https://api.vouchergalaxy.com/api/v1/external/payment-link`  
**Method:** `POST`  
**Content-Type:** `application/json`

---

## 2. Authentication & Security

All requests must be signed to ensure authenticity.

### header: `X-Signature`
You must include an `X-Signature` header in your request. This signature is generating using **HMAC-SHA256**.

**How to generate the signature:**
1.  Take your **Request Body** exactly as it will be sent (as a JSON string).
2.  Use your **Secret API Key** to hash the body using **HMAC-SHA256**.
3.  The resulting hex digest is your signature.

> **Note:** The signature relies on the *exact* string representation of your JSON body. Any extra spaces or key reordering will result in an `Invalid Signature` error.

---

## 3. Request Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | string | Yes | Customer's phone with country code (e.g., `+971501234567`) |
| `amount` | decimal | Yes | Transaction amount (e.g., `100.00`) |
| `currency` | string | Yes | 3-letter currency code (e.g., `AED`, `USD`) |
| `first_name` | string | No | Customer's first name |
| `second_name` | string | No | Customer's last name |
| `reference_id` | string | No | Your internal Order ID for reconciliation |
| `return_url` | url | No | URL to redirect the user to after success |
| `webhook_url` | url | No | SERVER URL to receive status updates |

---

## 4. cURL Examples

### Example 1: Standard Request (AED)
```bash
curl -X POST https://api.vouchergalaxy.com/api/v1/external/payment-link \
  -H 'Content-Type: application/json' \
  -H 'X-Signature: YOUR_CALCULATED_SIGNATURE' \
  -d '{"phone_number": "+971501234567", "amount": 100.00, "currency": "AED", "reference_id": "ORD-001", "webhook_url": "https://your-site.com/webhook"}'
```

### Example 2: USD Request
```bash
curl -X POST https://api.vouchergalaxy.com/api/v1/external/payment-link \
  -H 'Content-Type: application/json' \
  -H 'X-Signature: YOUR_CALCULATED_SIGNATURE' \
  -d '{"phone_number": "+15550199000", "amount": 50.00, "currency": "USD", "reference_id": "ORD-002"}'
```

### Example 3: Python Script for Signing
```python
import hmac
import hashlib
import json
import requests

API_KEY = "your-api-key"
URL = "https://api.vouchergalaxy.com/api/v1/external/payment-link"

payload = {
    "phone_number": "+971501234567",
    "amount": 100.00,
    "currency": "AED",
    "reference_id": "ORD-001"
}

# Ensure compact JSON
body_data = json.dumps(payload, separators=(',', ':'))

signature = hmac.new(
    API_KEY.encode(),
    body_data.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Signature": signature
}

requests.post(URL, data=body_data, headers=headers)
```

---

## 5. Webhook Notifications

If you provide a `webhook_url` in the request, our server will send a POST request to that URL when the payment Status changes (Success/Failure).

**Method:** `POST`  
**Security:** The webhook request will also contain an `x-signature` header signed with your API Key, so you can verify it comes from us.

### Webhook Payload (Success)
```json
{
  "order_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "status": "success",
  "amount": 100.0,
  "currency": "USD",
  "payment_id": "pi_3Q...", 
  "failure_reason": null
}
```

### Webhook Payload (Failure)
```json
{
  "order_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "status": "failed",
  "amount": 100.0,
  "currency": "USD",
  "payment_id": "pi_3Q...",
  "failure_reason": "Insufficient funds"
}
```

**Field Descriptions:**
*   `order_id`: The unique Order ID in our system.
*   `status`: `success` or `failed`.
*   `payment_id`: The Transaction ID from the Payment Provider.
*   `failure_reason`: Description of why the payment failed (if applicable).
