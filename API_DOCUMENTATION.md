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
    "full_name": "Test User"
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
{"access_token": "eyJhbGciOiJIUzI1NiIsInR...", "token_type": "bearer"}
```

---

## User Profile

### Get Profile
```bash
curl http://156.67.216.229/user/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:**
```json
{
  "id": "uuid",
  "phone_number": "+917907975711",
  "full_name": "Afsal Basheer",
  "email": "afsal@example.com",
  "date_of_birth": "1990-01-15",
  "gender": "Male",
  "country_of_residence": "India",
  "home_address": "123 Main Street",
  "town": "Mumbai",
  "state_province": "Maharashtra",
  "postal_code": "400001",
  "address_country": "India",
  "role": "ADMIN",
  "is_active": true
}
```

### Update Profile (Password Required)
```bash
curl -X PUT http://156.67.216.229/user/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "current_password": "afsal@123",
    "full_name": "Afsal Basheer",
    "email": "afsal@example.com",
    "date_of_birth": "1990-01-15",
    "gender": "Male",
    "country_of_residence": "India",
    "home_address": "123 Main Street",
    "town": "Mumbai",
    "state_province": "Maharashtra",
    "postal_code": "400001",
    "address_country": "India",
    "new_password": "newpassword123"
  }'
```

**Profile Fields:**
| Field | Type | Description |
|-------|------|-------------|
| current_password | string | Required for any update |
| full_name | string | User's full name |
| email | string | Email address |
| date_of_birth | date | Format: YYYY-MM-DD |
| gender | string | Male/Female/Other |
| country_of_residence | string | Country |
| home_address | string | Street address |
| town | string | City/Town |
| state_province | string | State/Province |
| postal_code | string | Zip/Postal code |
| address_country | string | Address country |
| new_password | string | Optional password change |

---

## User Coupons

### Claim Coupon
```bash
curl -X POST http://156.67.216.229/coupons/{coupon_id}/claim \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:**
```json
{"message": "Coupon claimed successfully", "coupon_id": "uuid"}
```

### Get My Claimed Coupons
```bash
curl http://156.67.216.229/user/coupons \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Response:**
```json
[{
  "id": "uuid",
  "user_id": "uuid",
  "coupon_id": "uuid",
  "claimed_at": "2026-02-03T21:09:21",
  "coupon": {
    "id": "uuid",
    "code": "SAVE20",
    "title": "20% Off",
    "discount_type": "percentage",
    "discount_amount": 20.0
  }
}]
```

---

## Coupons (Admin)

### List All Coupons
```bash
curl "http://156.67.216.229/coupons/?skip=0&limit=10&active_only=true"
```

### Get Coupon by ID
```bash
curl http://156.67.216.229/coupons/{coupon_id}
```

### Create Coupon (Admin)
```bash
curl -X POST http://156.67.216.229/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "code": "SAVE20",
    "title": "20% Off First Order",
    "description": "Get 20% off",
    "discount_type": "percentage",
    "discount_amount": 20.0,
    "min_purchase": 50.0,
    "max_uses": 100,
    "expiration_date": "2026-12-31T23:59:59"
  }'
```

### Update Coupon (Admin)
```bash
curl -X PUT http://156.67.216.229/coupons/{coupon_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Updated Title", "discount_amount": 25.0}'
```

### Delete Coupon (Admin)
```bash
curl -X DELETE http://156.67.216.229/coupons/{coupon_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Health Check
```bash
curl http://156.67.216.229/
```

---

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized / Incorrect password |
| 403 | Forbidden (not admin) |
| 404 | Not Found |
| 422 | Validation Error |

---

## Admin Credentials
**Phone:** +917907975711  
**Password:** afsal@123
