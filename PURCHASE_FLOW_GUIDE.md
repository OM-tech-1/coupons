# VoucherGalaxy - Internal Purchase Flow API Guide

**Base URL:** `https://api.vouchergalaxy.com`

This document covers the complete internal purchase flow: **Login → Add to Cart → Checkout → Payment Init → Payment Redirect**.

---

## Flow Overview

```
1. Login          → Get access token
2. List Coupons   → Find coupon to purchase
3. Add to Cart    → Add coupon to cart
4. Checkout       → Create a pending order
5. Payment Init   → Get Stripe payment URL
6. Redirect       → User completes payment on Stripe
7. Webhook        → Backend updates order to "paid"
```

---

## Step 1: Login

**Endpoint:** `POST /auth/login`

```bash
curl -X POST https://api.vouchergalaxy.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "country_code": "+91",
    "number": "7907975711",
    "password": "afsal@123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Note:** Use the `access_token` value in the `Authorization` header for all subsequent requests as `Bearer <token>`.

---

## Step 2: List Available Coupons

**Endpoint:** `GET /coupons/`

```bash
curl -X GET https://api.vouchergalaxy.com/coupons/
```

**Response (simplified):**
```json
[
  {
    "id": "eba0b551-4858-460f-b35c-246278928784",
    "code": "PETLOVE60",
    "title": "Updated Title",
    "price": 20.0,
    "discount_type": "percentage",
    "discount_amount": 60.0,
    "is_active": true
  }
]
```

> **Note:** Use the `id` field (UUID) of the coupon you want to purchase. Only coupons with `price > 0` will trigger the Stripe payment flow.

---

## Step 3: Add to Cart

**Endpoint:** `POST /cart/add`  
**Auth:** Required

```bash
curl -X POST https://api.vouchergalaxy.com/cart/add \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "coupon_id": "eba0b551-4858-460f-b35c-246278928784",
    "quantity": 1
  }'
```

**Response:**
```json
{
  "message": "Added to cart",
  "coupon_id": "eba0b551-4858-460f-b35c-246278928784"
}
```

---

## Step 4: Checkout (Create Order)

**Endpoint:** `POST /orders/checkout`  
**Auth:** Required

```bash
curl -X POST https://api.vouchergalaxy.com/orders/checkout \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "payment_method": "stripe"
  }'
```

**Response:**
```json
{
  "id": "62a17be8-ec26-45ab-a70d-504d849bcfee",
  "user_id": "3f254d9d-3d5b-4963-85d3-8710d4014409",
  "total_amount": 20.0,
  "status": "pending_payment",
  "payment_id": null,
  "payment_method": "stripe",
  "created_at": "2026-02-12T19:54:26.052479",
  "items": [
    {
      "id": "15ae50b3-0c90-4fde-a339-5f9c7cda76de",
      "coupon_id": "eba0b551-4858-460f-b35c-246278928784",
      "quantity": 1.0,
      "price": 20.0,
      "coupon": {
        "code": "PETLOVE60",
        "title": "Updated Title",
        "description": "Amazing deal on all pet food",
        "discount_type": "percentage",
        "is_active": true
      },
      "coupon_title": "Updated Title",
      "coupon_description": "Amazing deal on all pet food",
      "coupon_type": "percentage"
    }
  ]
}
```

> **Important:** Save the `id` field — this is the **Order ID** needed for the next step.  
> The status will be `"pending_payment"` until payment is completed.

---

## Step 5: Initialize Payment

**Endpoint:** `POST /payments/init`  
**Auth:** Required

```bash
curl -X POST https://api.vouchergalaxy.com/payments/init \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "order_id": "62a17be8-ec26-45ab-a70d-504d849bcfee",
    "amount": 2000,
    "currency": "AED",
    "return_url": "https://yourapp.com/checkout/success"
  }'
```

### Request Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `order_id` | UUID | ✅ | Order ID from checkout response |
| `amount` | integer | ✅ | Amount in **smallest currency unit** (cents/fils). `20.00 AED` = `2000` |
| `currency` | string | ❌ | 3-letter currency code (default: `"USD"`) |
| `return_url` | string | ❌ | URL to redirect user after payment completion |

### Amount Conversion

| Actual Amount | Currency | Value to Send |
|---|---|---|
| 20.00 | AED/USD/EUR/GBP | `2000` |
| 10.50 | AED/USD/EUR/GBP | `1050` |
| 100.00 | AED/USD/EUR/GBP | `10000` |
| 500 | JPY (zero-decimal) | `500` |

**Response:**
```json
{
  "redirect_url": "https://payment.vouchergalaxy.com/pay?token=eyJhbGci...",
  "token": "eyJhbGci...",
  "expires_at": "2026-02-12T20:00:10.154281",
  "order_id": "62a17be8-ec26-45ab-a70d-504d849bcfee",
  "payment_intent_id": "pi_3T05yj4HBzURSPOU16WV5js9"
}
```

### Response Fields

| Field | Description |
|---|---|
| `redirect_url` | URL to redirect user to for payment (Stripe payment page) |
| `token` | Short-lived JWT token (expires in 5 minutes) |
| `expires_at` | Token expiration timestamp |
| `order_id` | The order being paid for |
| `payment_intent_id` | Stripe PaymentIntent ID for tracking |

---

## Step 6: Redirect User to Payment

Redirect the user's browser to the `redirect_url` from the previous step:

```
https://payment.vouchergalaxy.com/pay?token=eyJhbGci...
```

The user will see a Stripe payment form, enter their card details, and submit payment.

### After Payment

- **Success:** User is redirected to the `return_url` you provided in Step 5.
- **Failure:** User sees an error on the payment page and can retry.

---

## Step 7: Webhook (Automatic)

After successful payment, Stripe sends a webhook to the backend:

```
POST /webhooks/stripe → payment_intent.succeeded
```

The backend automatically:
1. Updates the order status from `"pending_payment"` → `"paid"`
2. Updates the payment record status to `"succeeded"`
3. Dispatches any configured outbound webhooks

**No action is required from the frontend for this step.**

---

## Checking Order Status

**Endpoint:** `GET /orders/{order_id}`  
**Auth:** Required

```bash
curl -X GET https://api.vouchergalaxy.com/orders/62a17be8-ec26-45ab-a70d-504d849bcfee \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

### Order Status Values

| Status | Meaning |
|---|---|
| `pending_payment` | Order created, awaiting payment |
| `paid` | Payment successful, coupons delivered |
| `failed` | Payment failed |

---

## Checking Payment Status

**Endpoint:** `GET /payments/status/{order_id}`

```bash
curl -X GET https://api.vouchergalaxy.com/payments/status/62a17be8-ec26-45ab-a70d-504d849bcfee
```

**Response:**
```json
{
  "order_id": "62a17be8-ec26-45ab-a70d-504d849bcfee",
  "status": "succeeded",
  "amount": 2000,
  "currency": "AED",
  "paid_at": "2026-02-12T20:01:15.123456",
  "gateway": "stripe"
}
```

---

## Error Responses

| HTTP Code | Detail | Meaning |
|---|---|---|
| `400` | `"Cart is empty"` | No items in cart before checkout |
| `400` | `"Payment initialization failed"` | Invalid order ID or Stripe error |
| `401` | `"Not authenticated"` | Missing or expired token |
| `404` | `"Order not found"` | Order ID doesn't exist or doesn't belong to user |
