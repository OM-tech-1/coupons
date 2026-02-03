# Coupon App API Documentation

**Base URL:** `http://156.67.216.229`

**Swagger UI:** http://156.67.216.229/docs

---

## Authentication

### Register User
```bash
curl -X POST http://156.67.216.229/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "+91",
    "number": "9876543210",
    "password": "mypassword123",
    "full_name": "Test User",
    "second_name": "Account"
  }'
```

### Login
```bash
curl -X POST http://156.67.216.229/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "country_code": "+91",
    "number": "7907975711",
    "password": "afsal@123"
  }'
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer"
}
```

---

## Coupons

### List All Coupons
```bash
curl http://156.67.216.229/coupons/
```

**With filters:**
```bash
curl "http://156.67.216.229/coupons/?skip=0&limit=10&active_only=true"
```

### Get Coupon by ID
```bash
curl http://156.67.216.229/coupons/{coupon_id}
```

**Example:**
```bash
curl http://156.67.216.229/coupons/1ba6b75b-e4bd-45e3-9b84-ec6934b7e35c
```

### Create Coupon (Admin Only)
```bash
curl -X POST http://156.67.216.229/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "code": "SAVE20",
    "title": "20% Off First Order",
    "description": "Get 20% off your first order",
    "discount_type": "percentage",
    "discount_amount": 20.0,
    "min_purchase": 50.0,
    "max_uses": 100,
    "expiration_date": "2026-12-31T23:59:59"
  }'
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| code | string | Yes | Unique coupon code (3-50 chars) |
| title | string | Yes | Coupon title (3-100 chars) |
| description | string | No | Detailed description |
| discount_type | string | No | "percentage" or "fixed" (default: percentage) |
| discount_amount | float | Yes | Discount value (> 0) |
| min_purchase | float | No | Minimum purchase amount (default: 0) |
| max_uses | int | No | Max redemptions (null = unlimited) |
| expiration_date | datetime | No | Expiry date (ISO 8601) |

### Update Coupon (Admin Only)
```bash
curl -X PUT http://156.67.216.229/coupons/{coupon_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Updated: 25% Off",
    "discount_amount": 25.0,
    "is_active": true
  }'
```

### Delete Coupon (Admin Only)
```bash
curl -X DELETE http://156.67.216.229/coupons/{coupon_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:** HTTP 204 No Content

---

## Health Check
```bash
curl http://156.67.216.229/
```
**Response:**
```json
{"status": "OK"}
```

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request (validation error, duplicate code) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (not admin) |
| 404 | Not Found |
| 422 | Validation Error |

---

## Admin User

**Phone:** +917907975711  
**Password:** afsal@123
