# Coupon App API Documentation

**Base URL:** `https://api.vouchergalaxy.com`  
**Swagger UI:** https://api.vouchergalaxy.com/docs  
**Version:** `2.0.1`

> All authenticated endpoints require `Authorization: Bearer <access_token>` header.  
> Rate limits are noted per endpoint. Exceeding them returns `429 Too Many Requests`.

---

## Table of Contents
1. [Authentication](#authentication)
2. [User Profile & Wallet](#user-profile--wallet)
3. [Categories](#categories)
4. [Regions](#regions)
5. [Countries](#countries)
6. [Coupons](#coupons)
7. [Packages (Bundles)](#packages-bundles)
8. [Cart](#cart)
9. [Orders](#orders)
10. [Contact / Support](#contact--support)
11. [Stripe Payments](#stripe-payments)
12. [External Payment API](#external-payment-api)
13. [Real-Time Features (Redis)](#real-time-features-redis)
14. [Admin](#admin)
15. [Health](#health)
16. [Error Codes](#error-codes)

---

## Authentication

**Rate Limit:** Register/Login = 10/min; Change-password/Forgot/Reset = 5/min

### Register (Unified)
`POST /auth/register`
```bash
curl -X POST https://api.vouchergalaxy.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "country_code": "+91",
    "number": "9876543210",
    "password": "pass123",
    "full_name": "Test User"
  }'
```
**Response** `201`:
```json
{
  "id": "uuid",
  "phone_number": "+919876543210",
  "full_name": "Test User",
  "email": "user@example.com",
  "role": "USER",
  "is_active": true
}
```
**Error:** `400` if email or phone already registered.

---

### Login (Unified)
`POST /auth/login`  
Supports login by email **or** phone number — provide one or the other.
```bash
# Login by email
curl -X POST https://api.vouchergalaxy.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'

# Login by phone
curl -X POST https://api.vouchergalaxy.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"country_code": "+91", "number": "9876543210", "password": "pass123"}'
```
**Response** `200`:
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```
**JWT token includes** a `currency` claim derived from the user's country code (e.g., `"currency": "INR"` for +91 numbers; `"USD"` for email-only users).  
**Error:** `401` on bad credentials.

---

### Change Password
`POST /auth/change-password` 🔒  
Rate limit: 5/min
```bash
curl -X POST https://api.vouchergalaxy.com/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "current_password": "OldPassword123",
    "new_password": "NewSecurePassword456!"
  }'
```
**Response** `200`:
```json
{"success": true, "message": "Password updated successfully"}
```
**Error:** `403` if `current_password` is incorrect.

---

### Forgot Password
`POST /auth/forgot-password`  
Rate limit: 5/min. Always returns success (does not reveal if email exists).
```bash
curl -X POST https://api.vouchergalaxy.com/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```
**Response** `200`:
```json
{"success": true, "message": "If that email is registered, a password reset link has been sent."}
```
**Behavior:** Sends an email with a magic link containing a JWT token. Email is sent asynchronously (background task).

---

### Reset Password
`POST /auth/reset-password`  
Rate limit: 5/min
```bash
curl -X POST https://api.vouchergalaxy.com/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "JWT_TOKEN_FROM_EMAIL",
    "new_password": "NewSecurePassword123!"
  }'
```
**Response** `200`:
```json
{"success": true, "message": "Password successfully reset."}
```
**Notes:** Token is single-use and expires in 15 minutes. Returns `400` for invalid/expired/already-used tokens.

---

## User Profile & Wallet

### Get My Profile
`GET /user/me` 🔒
```bash
curl https://api.vouchergalaxy.com/user/me -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
{
  "id": "uuid",
  "phone_number": "+919876543210",
  "full_name": "Test User",
  "second_name": null,
  "email": "user@example.com",
  "date_of_birth": "1995-06-15",
  "gender": "male",
  "country_of_residence": "India",
  "home_address": "123 Main Street",
  "town": "Bangalore",
  "state_province": "Karnataka",
  "postal_code": "560001",
  "address_country": "India",
  "role": "USER",
  "is_active": true
}
```

---

### Update My Profile
`PUT /user/me` 🔒  
All fields are optional. Provide only fields you want to update.
```bash
curl -X PUT https://api.vouchergalaxy.com/user/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "full_name": "New Name",
    "second_name": "Kumar",
    "email": "newemail@example.com",
    "date_of_birth": "1995-06-15",
    "gender": "male",
    "country_of_residence": "India",
    "home_address": "123 Main Street",
    "town": "Bangalore",
    "state_province": "Karnataka",
    "postal_code": "560001",
    "address_country": "India",
    "current_password": "OldPass123",
    "new_password": "NewPass456!"
  }'
```
**Note:** `current_password` + `new_password` are optional and used only when changing password via profile update.  
**Response** `200`: Same shape as Get My Profile.

---

### Get My Claimed Coupons
`GET /user/coupons` 🔒
```bash
curl https://api.vouchergalaxy.com/user/coupons -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "coupon_id": "uuid",
    "claimed_at": "2026-02-04T12:00:00",
    "coupon": {
      "id": "uuid",
      "code": "MCDEAL50",
      "redeem_code": "ABC123XYZ",
      "brand": "McDonald's",
      "title": "50% off any meal",
      "description": "Valid at all outlets",
      "discount_type": "percentage",
      "discount_amount": 50.0,
      "expiration_date": "2026-12-31T00:00:00"
    }
  }
]
```

---

### Get Single Claimed Coupon Detail
`GET /user/coupons/{coupon_id}` 🔒
```bash
curl https://api.vouchergalaxy.com/user/coupons/{coupon_id} -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
{
  "id": "uuid",
  "coupon_id": "uuid",
  "code": "MCDEAL50",
  "redeem_code": "ABC123XYZ",
  "brand": "McDonald's",
  "title": "50% off any meal",
  "description": "Valid at all outlets",
  "discount_type": "percentage",
  "discount_amount": 50.0,
  "category": {"id": "uuid", "name": "Food & Grocery"},
  "is_active": true,
  "purchased_date": "2026-02-04T12:00:00",
  "expires_date": "2026-12-31T00:00:00",
  "status": "active"
}
```
**Status values:** `active`, `used`, `expired`

---

### Mark Coupon as Used
`POST /user/coupons/{coupon_id}/mark-used` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/user/coupons/{coupon_id}/mark-used \
  -H "Authorization: Bearer TOKEN"
```
**Response** `200`: Same shape as Get Single Claimed Coupon Detail with `status: "used"`.

---

### Get Wallet Summary
`GET /user/wallet` 🔒
```bash
curl https://api.vouchergalaxy.com/user/wallet -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
{
  "total_coupons": 12,
  "active": 8,
  "used": 3,
  "expired": 1
}
```

---

### Get Wallet Coupons
`GET /user/wallet/coupons` 🔒  
Full list of all coupons in the user's wallet.
```bash
curl https://api.vouchergalaxy.com/user/wallet/coupons -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
[
  {
    "id": "uuid",
    "coupon_id": "uuid",
    "code": "MCDEAL50",
    "redeem_code": "ABC123XYZ",
    "brand": "McDonald's",
    "title": "50% off any meal",
    "description": "Valid at all outlets",
    "category": {"id": "uuid", "name": "Food & Grocery"},
    "is_active": true,
    "purchased_date": "2026-02-04T12:00:00",
    "expires_date": "2026-12-31T00:00:00",
    "status": "active"
  }
]
```

---

## Categories

### List All Categories
`GET /categories/`
```bash
curl "https://api.vouchergalaxy.com/categories/?active_only=true"
```
**Query Params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `active_only` | bool | true | Return only active categories |

**Response** `200`:
```json
[
  {"id": "uuid", "name": "Food & Grocery", "slug": "food-grocery", "description": "...", "icon": "🍔", "display_order": 1, "is_active": true}
]
```

---

### List Categories with Coupon Counts
`GET /categories/with-counts`
```bash
curl "https://api.vouchergalaxy.com/categories/with-counts?active_only=true"
```
**Response**: Same as List All Categories but with `coupon_count: int` added.

---

### Get Category by Slug
`GET /categories/{slug}`
```bash
curl https://api.vouchergalaxy.com/categories/food-grocery
```

---

### Browse Coupons in Category
`GET /categories/{slug}/coupons`
```bash
curl "https://api.vouchergalaxy.com/categories/food-grocery/coupons?limit=20&skip=0&active_only=true"
```
**Query Params:** `skip`, `limit` (1–100), `active_only`  
**Note:** Currency auto-detected from user's JWT token if logged in; defaults to USD.

---

### Create Category *(Admin)*
`POST /categories/` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/categories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Sports & Fitness",
    "slug": "sports-fitness",
    "description": "Sports equipment and fitness products",
    "icon": "⚽",
    "display_order": 11,
    "is_active": true
  }'
```
**Response** `201`: Category object. **Error:** `400` if slug already exists.

---

### Update Category *(Admin)*
`PUT /categories/{category_id}` 🔒  
All fields optional.
```bash
curl -X PUT https://api.vouchergalaxy.com/categories/{category_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name": "Updated Name", "is_active": false}'
```

---

### Delete Category *(Admin)*
`DELETE /categories/{category_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/categories/{category_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `204 No Content`.

---

## Regions

### List All Regions with Countries
`GET /regions/`
```bash
curl "https://api.vouchergalaxy.com/regions/?active_only=true"
```
**Response** `200`:
```json
[
  {
    "id": "uuid",
    "name": "Middle East",
    "slug": "middle-east",
    "countries": [
      {"id": "uuid", "name": "UAE", "slug": "united-arab-emirates", "country_code": "AE"}
    ]
  }
]
```

---

### Get Region by Slug
`GET /regions/{slug}`
```bash
curl https://api.vouchergalaxy.com/regions/middle-east
```

---

### Browse Coupons in Region
`GET /regions/{slug}/coupons` — see category coupons for same params.
```bash
curl "https://api.vouchergalaxy.com/regions/middle-east/coupons?limit=20"
```

---

### Create Region *(Admin)*
`POST /regions/` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/regions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name": "South Asia", "slug": "south-asia", "is_active": true}'
```
**Response** `201`: Region object.

---

### Update Region *(Admin)*
`PUT /regions/{region_id}` 🔒  
All fields optional.
```bash
curl -X PUT https://api.vouchergalaxy.com/regions/{region_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name": "Updated Name"}'
```

---

### Delete Region *(Admin)*
`DELETE /regions/{region_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/regions/{region_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `204 No Content`.

---

## Countries

### List All Countries
`GET /countries/`
```bash
curl "https://api.vouchergalaxy.com/countries/?region_id=REGION_UUID&active_only=true"
```
**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `region_id` | UUID | Filter by region |
| `active_only` | bool | Default: true |

**Response** `200`:
```json
[
  {"id": "uuid", "name": "UAE", "slug": "united-arab-emirates", "country_code": "AE", "region_id": "uuid", "is_active": true}
]
```

---

### Get Country by Slug
`GET /countries/{slug}`
```bash
curl https://api.vouchergalaxy.com/countries/united-arab-emirates
```

---

### Browse Coupons in Country
`GET /countries/{slug}/coupons`
```bash
curl "https://api.vouchergalaxy.com/countries/united-arab-emirates/coupons?limit=20"
```

---

### Create Country *(Admin)*
`POST /countries/` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/countries/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Saudi Arabia",
    "slug": "saudi-arabia",
    "country_code": "SA",
    "region_id": "REGION_UUID",
    "is_active": true
  }'
```
**Response** `201`: Country object.  
**Error:** `400` if slug or country_code already exists.

---

### Update Country *(Admin)*
`PUT /countries/{country_id}` 🔒  
All fields optional.
```bash
curl -X PUT https://api.vouchergalaxy.com/countries/{country_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name": "KSA", "is_active": true}'
```

---

### Delete Country *(Admin)*
`DELETE /countries/{country_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/countries/{country_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `204 No Content`.

---

## Coupons

**Multi-Currency:** Currency is auto-detected from the `currency` claim in the JWT token (e.g., `INR` for +91). Anonymous users default to `USD`. Response includes `currency_symbol` and adjusted `price`/`discount_amount`.

### List Coupons
`GET /coupons/`
```bash
curl "https://api.vouchergalaxy.com/coupons/?skip=0&limit=20&active_only=true&category_id=UUID&is_featured=true&search=pizza&min_discount=10"
```
**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 100 | Max results (1–100) |
| `active_only` | bool | true | Show only active coupons |
| `category_id` | UUID | — | Filter by category |
| `search` | string | — | Search title, brand, or code |
| `is_featured` | bool | — | Filter featured coupons |
| `min_discount` | float | — | Minimum discount amount |

**Response** `200`:
```json
[
  {
    "id": "uuid",
    "code": "PETLOVE50",
    "title": "50% off pet food",
    "brand": "PetStore",
    "description": "Valid in-store only",
    "discount_type": "percentage",
    "discount_amount": 50.0,
    "price": 2.99,
    "currency": "USD",
    "currency_symbol": "$",
    "picture_url": "https://s3-url/image.jpg",
    "availability_type": "local",
    "is_active": true,
    "is_featured": false,
    "expiration_date": "2026-12-31T00:00:00",
    "category": {"id": "uuid", "name": "Pets"},
    "pricing": {
      "INR": {"price": 250, "discount_amount": 50},
      "AED": {"price": 10, "discount_amount": 2}
    }
  }
]
```

---

### Get Coupon by ID
`GET /coupons/{coupon_id}`
```bash
curl "https://api.vouchergalaxy.com/coupons/{coupon_id}"
```
**Response** `200`: Single coupon object (same shape as list item).

---

### Create Coupon *(Admin)*
`POST /coupons/` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "code": "PETLOVE50",
    "redeem_code": "ABC123XYZ",
    "brand": "PetStore",
    "title": "50% off pet food",
    "description": "Valid in-store only",
    "discount_type": "percentage",
    "discount_amount": 50.0,
    "price": 2.99,
    "category_id": "CATEGORY_UUID",
    "availability_type": "local",
    "country_ids": ["COUNTRY_UUID_1", "COUNTRY_UUID_2"],
    "picture_url": "https://s3-url/image.jpg",
    "is_active": true,
    "is_featured": false,
    "expiration_date": "2026-12-31T00:00:00",
    "pricing": {
      "INR": {"price": 250, "discount_amount": 50},
      "AED": {"price": 10, "discount_amount": 2},
      "SAR": {"price": 11, "discount_amount": 2},
      "OMR": {"price": 1.2, "discount_amount": 0.3},
      "USD": {"price": 2.99, "discount_amount": 0.5}
    }
  }'
```
**`availability_type`:** `online`, `local`, or `both`.  
**Note:** If the `code` matches a soft-deleted coupon, it gets restored instead of creating a duplicate.

---

### Update Coupon *(Admin)*
`PUT /coupons/{coupon_id}` 🔒  
All fields optional.
```bash
curl -X PUT https://api.vouchergalaxy.com/coupons/{coupon_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "redeem_code": "NEWCODE456",
    "price": 5.99,
    "is_featured": true,
    "category_id": "CATEGORY_UUID",
    "pricing": {"INR": {"price": 499, "discount_amount": 50}}
  }'
```

---

### Delete Coupon *(Admin)*
`DELETE /coupons/{coupon_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/coupons/{coupon_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `204 No Content`.

---

### Claim Coupon 🔒
`POST /coupons/{coupon_id}/claim`
```bash
curl -X POST https://api.vouchergalaxy.com/coupons/{coupon_id}/claim \
  -H "Authorization: Bearer TOKEN"
```
**Response** `201`:
```json
{"message": "Coupon claimed successfully", "coupon_id": "uuid"}
```
**Error:** `400` if already claimed, out of stock, or unavailable.

---

### Track Coupon View *(Public)*
`POST /coupons/{coupon_id}/view`  
No auth required. Feeds Redis trending and recently-viewed.
```bash
curl -X POST "https://api.vouchergalaxy.com/coupons/{coupon_id}/view?session_id=SESSION_123"
```
**Query Params:** `session_id` (optional) — used for anonymous recently-viewed tracking.  
**Response** `201`:
```json
{"message": "View tracked", "coupon_id": "uuid"}
```

---

### Get Real-Time Stock *(Public)*
`GET /coupons/{coupon_id}/stock`
```bash
curl "https://api.vouchergalaxy.com/coupons/{coupon_id}/stock"
```
**Response** `200`:
```json
{"coupon_id": "uuid", "stock": 45}
```

---

### Get Trending Coupons *(Public)*
`GET /coupons/trending`
```bash
curl "https://api.vouchergalaxy.com/coupons/trending?limit=10&period=24h"
```
**Query Params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 10 | Max results (1–50) |
| `period` | string | `24h` | Trending window: `24h` or `7d` |

---

### Get Featured Coupons *(Public)*
`GET /coupons/featured`
```bash
curl "https://api.vouchergalaxy.com/coupons/featured?limit=10"
```
**Query Params:** `limit` (1–50, default 10).

---

### Get Recently Viewed *(Public)*
`GET /coupons/recently-viewed`
```bash
curl "https://api.vouchergalaxy.com/coupons/recently-viewed?session_id=SESSION_123&limit=20"
```
**Query Params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | ✅ | Session or user ID used when tracking views |
| `limit` | int | — | Max results (1–50, default 20) |

---

### Upload Coupon Image *(Admin)*
`POST /upload/image` 🔒  
Uploads to S3 and returns the URL.
```bash
curl -X POST https://api.vouchergalaxy.com/upload/image \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "file=@/path/to/image.jpg"
```
**Response** `200`:
```json
{"url": "https://s3-bucket-url/coupons/image.jpg"}
```

---

## Packages (Bundles)

Packages group multiple coupons into a single purchasable bundle with optional discounting. Slugs are **not unique** — multiple packages can share the same slug.

### List Packages
`GET /packages/`
```bash
curl "https://api.vouchergalaxy.com/packages/?is_featured=true&country=UAE&filter=highest_saving&brands=McDonald%27s&brands=KFC"
```
**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 100 | Max results (1–100) |
| `category_id` | UUID | — | Filter by category |
| `is_active` | bool | true | Filter active/inactive |
| `is_featured` | bool | — | Filter featured packages |
| `filter` | string | — | Sort: `highest_saving`, `newest`, `avg_rating`, `bundle_sold` |
| `brands` | string[] | — | Filter by brand names (multiple allowed) |
| `country` | string | — | Filter by country (e.g. `UAE`, `KSA`, `Kuwait`, `Bahrain`, `Oman`) |

**Response** `200` (lightweight — no nested coupons):
```json
[
  {
    "id": "uuid",
    "name": "Dining Bundle",
    "slug": "dining-bundle",
    "description": "Best dining deals in UAE",
    "brand": "Gulf Eats",
    "brand_url": "https://gulfeats.com",
    "discount": 15.0,
    "avg_rating": 4.3,
    "total_sold": 120,
    "is_active": true,
    "is_featured": false,
    "is_trending": false,
    "country": "UAE",
    "category_id": "uuid",
    "category": {"id": "uuid", "name": "Food & Grocery", "slug": "food-grocery"},
    "coupon_count": 5,
    "pricing": {"USD": 25.0, "AED": 92.0, "INR": 2080.0},
    "final_prices": {"USD": 21.25, "AED": 78.2, "INR": 1768.0},
    "max_saving": 15.0,
    "expiration_date": "2026-12-31T00:00:00",
    "created_at": "2026-01-15T10:00:00"
  }
]
```

---

### Get Package by ID
`GET /packages/{package_id}`  
Full response including nested coupons with per-currency pricing.
```bash
curl "https://api.vouchergalaxy.com/packages/{package_id}"
```
**Response** `200`: Same as list item but with `coupons` array instead of `coupon_count`.
```json
{
  "id": "uuid",
  "name": "Dining Bundle",
  "coupons": [
    {
      "id": "uuid",
      "title": "10% off burger",
      "brand": "McDonald's",
      "discount_type": "percentage",
      "discount_amount": 10.0,
      "picture_url": "https://...",
      "is_active": true,
      "pricing": {"USD": 5.0, "AED": 18.5},
      "discounts": {"USD": 0.5, "AED": 1.85}
    }
  ],
  "pricing": {"USD": 25.0, "AED": 92.0},
  "final_prices": {"USD": 21.25, "AED": 78.2},
  "..."
}
```

---

### Get Coupons in Package
`GET /packages/{package_id}/coupons`
```bash
curl "https://api.vouchergalaxy.com/packages/{package_id}/coupons"
```
**Response** `200`: Array of `CouponPublicResponse` objects.

---

### Create Package *(Admin)*
`POST /packages/` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/packages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Dining Bundle",
    "slug": "dining-bundle",
    "description": "Best dining deals in UAE",
    "brand": "Gulf Eats",
    "brand_url": "https://gulfeats.com",
    "discount": 15.0,
    "avg_rating": 0.0,
    "total_sold": 0,
    "category_id": "CATEGORY_UUID",
    "country": "UAE",
    "is_active": true,
    "is_featured": false,
    "is_trending": false,
    "expiration_date": "2026-12-31T00:00:00",
    "coupon_ids": ["COUPON_UUID_1", "COUPON_UUID_2"]
  }'
```
**Note:** If a soft-deleted package with the same `slug` exists, it is restored with the new data.  
**Response** `201`: Full PackageResponse.

---

### Update Package *(Admin)*
`PUT /packages/{package_id}` 🔒  
All fields optional.
```bash
curl -X PUT https://api.vouchergalaxy.com/packages/{package_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Updated Bundle Name",
    "discount": 20.0,
    "is_featured": true,
    "is_trending": true,
    "coupon_ids": ["COUPON_UUID_1", "COUPON_UUID_3"]
  }'
```
**Note:** Providing `coupon_ids` replaces the entire coupon list.

---

### Delete Package *(Admin)*
`DELETE /packages/{package_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/packages/{package_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `204 No Content`.

---

### Add Coupons to Package *(Admin)*
`POST /packages/{package_id}/coupons` 🔒
```bash
curl -X POST https://api.vouchergalaxy.com/packages/{package_id}/coupons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '["COUPON_UUID_1", "COUPON_UUID_2"]'
```
**Note:** Adds to existing coupons (does not replace).  
**Response** `200`: Full PackageResponse.

---

### Remove Coupon from Package *(Admin)*
`DELETE /packages/{package_id}/coupons/{coupon_id}` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/packages/{package_id}/coupons/{coupon_id} \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`: Full PackageResponse with the coupon removed.

---

## Cart

Cart supports both individual **coupons** and **packages (bundles)**. Provide exactly one of `coupon_id` or `package_id`.

### Add to Cart
`POST /cart/add` 🔒
```bash
# Add a coupon
curl -X POST https://api.vouchergalaxy.com/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"coupon_id": "COUPON_UUID", "quantity": 1}'

# Add a package/bundle
curl -X POST https://api.vouchergalaxy.com/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"package_id": "PACKAGE_UUID", "quantity": 1}'
```
**Response** `201` (coupon): `{"message": "...", "coupon_id": "uuid"}`  
**Response** `201` (package): `{"message": "...", "package_id": "uuid"}`

---

### View Cart
`GET /cart/` 🔒
```bash
curl https://api.vouchergalaxy.com/cart/ -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "coupon_id": "uuid",
      "package_id": null,
      "quantity": 1,
      "added_at": "2026-03-23T10:00:00",
      "coupon": {
        "id": "uuid", "code": "MCDEAL50", "title": "50% off burger",
        "currency": "USD", "currency_symbol": "$",
        "prices": {"USD": 5.0, "AED": 18.5},
        "discounts": {"USD": 0.5, "AED": 1.85}
      },
      "package": null,
      "prices": {"USD": 5.0, "AED": 18.5},
      "final_prices": {"USD": 5.0, "AED": 18.5}
    }
  ],
  "total_items": 1,
  "total_amount": 5.0,
  "prices": {"USD": 5.0, "AED": 18.5},
  "final_prices": {"USD": 5.0, "AED": 18.5}
}
```

---

### Remove Item from Cart
`DELETE /cart/{item_id}` 🔒  
`item_id` is the cart item UUID (from `cart.items[].id`).
```bash
curl -X DELETE https://api.vouchergalaxy.com/cart/{item_id} \
  -H "Authorization: Bearer TOKEN"
```
**Response** `204 No Content`. **Error** `404` if item not in cart.

---

### Clear Cart
`DELETE /cart/` 🔒
```bash
curl -X DELETE https://api.vouchergalaxy.com/cart/ -H "Authorization: Bearer TOKEN"
```
**Response** `204 No Content`.

---

## Orders

### Checkout
`POST /orders/checkout` 🔒  
Creates an order from the current cart. Currency is determined from JWT token.
```bash
curl -X POST https://api.vouchergalaxy.com/orders/checkout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"payment_method": "mock"}'
```
**`payment_method`:** `mock` (test) or `stripe` (live).  
**Response** `200`:
```json
{
  "id": "uuid",
  "status": "paid",
  "total_amount": 9.99,
  "payment_method": "mock",
  "created_at": "2026-03-23T10:00:00",
  "items": [
    {"id": "uuid", "coupon_id": "uuid", "package_id": null, "quantity": 1, "unit_price": 9.99}
  ]
}
```

---

### Get My Orders
`GET /orders/` 🔒
```bash
curl https://api.vouchergalaxy.com/orders/ -H "Authorization: Bearer TOKEN"
```
**Response** `200`: Array of order objects.

---

### Get Order by ID
`GET /orders/{order_id}` 🔒
```bash
curl https://api.vouchergalaxy.com/orders/{order_id} -H "Authorization: Bearer TOKEN"
```

---

### Download Invoice PDF
`GET /orders/{order_id}/invoice` 🔒  
Returns a PDF file stream for the order.
```bash
curl https://api.vouchergalaxy.com/orders/{order_id}/invoice \
  -H "Authorization: Bearer TOKEN" \
  --output invoice.pdf
```
**Response** `200`: `Content-Type: application/pdf` with `Content-Disposition: attachment; filename=invoice_<short_id>.pdf`.

---

## Contact / Support

### Submit Contact Message *(Public)*
`POST /contact/`  
No authentication required.
```bash
curl -X POST https://api.vouchergalaxy.com/contact/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Issue with my order",
    "message": "I have not received my coupon codes after payment."
  }'
```
**Response** `201`:
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Issue with my order",
  "status": "pending",
  "created_at": "2026-03-23T10:00:00"
}
```

---

### List Contact Messages *(Admin)*
`GET /contact/admin` 🔒
```bash
curl "https://api.vouchergalaxy.com/contact/admin?skip=0&limit=20&status=pending&search=order" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `skip` | int | Pagination offset |
| `limit` | int | Max results 1–100 (default: 20) |
| `status` | string | Filter: `pending` or `resolved` |
| `search` | string | Search by name, email, or subject |

**Response** `200`:
```json
{
  "total": 42,
  "items": [
    {
      "id": "uuid", "name": "John Doe", "email": "john@example.com",
      "subject": "Issue with my order", "message": "...",
      "status": "pending", "created_at": "2026-03-23T10:00:00"
    }
  ],
  "skip": 0,
  "limit": 20
}
```

---

### Get Contact Message by ID *(Admin)*
`GET /contact/admin/{message_id}` 🔒
```bash
curl "https://api.vouchergalaxy.com/contact/admin/{message_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### Update Contact Message Status *(Admin)*
`PATCH /contact/admin/{message_id}` 🔒
```bash
curl -X PATCH "https://api.vouchergalaxy.com/contact/admin/{message_id}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"status": "resolved"}'
```
**`status` values:** `pending`, `resolved`.

---

## Stripe Payments

### Initialize Payment
`POST /payments/init` 🔒  
Creates a Stripe PaymentIntent. Currency is derived from the `currency` field you pass (the currency the user is viewing prices in).
```bash
curl -X POST https://api.vouchergalaxy.com/payments/init \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "order_id": "ORDER_UUID",
    "currency": "AED",
    "return_url": "https://vouchergalaxy.com/payment-success",
    "metadata": {"source": "web"}
  }'
```
**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | UUID | ✅ | Order to pay for |
| `currency` | string | ✅ | Currency code (USD, AED, INR, etc.) |
| `return_url` | string | — | Redirect URL after payment |
| `metadata` | object | — | Additional metadata for Stripe |

**Response** `200`:
```json
{
  "redirect_url": "https://payment.vouchergalaxy.com/pay?token=eyJ...",
  "token": "eyJ...",
  "expires_at": "2026-03-23T10:15:00",
  "order_id": "uuid",
  "payment_intent_id": "pi_..."
}
```
**Errors:** `400` if order not found, amount too small (<$0.50), or coupon out of stock. `403` if not the order owner.

---

### Validate Token *(Payment UI Use)*
`POST /payments/validate-token`  
No auth required. Called by the payment UI page.
```bash
curl -X POST https://api.vouchergalaxy.com/payments/validate-token \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJ..."}'
```
**Response** `200`:
```json
{
  "client_secret": "pi_..._secret_...",
  "publishable_key": "pk_live_...",
  "amount": 9225,
  "currency": "AED",
  "order_id": "uuid",
  "return_url": "https://vouchergalaxy.com/payment-success"
}
```
**Note:** `amount` is in the smallest currency unit (e.g., fils for AED, paise for INR, cents for USD).

---

### Get Payment Status
`GET /payments/status/{order_id}` 🔒  
Order owner or Admin only.
```bash
curl https://api.vouchergalaxy.com/payments/status/{order_id} \
  -H "Authorization: Bearer TOKEN"
```
**Response** `200`:
```json
{
  "order_id": "uuid",
  "status": "succeeded",
  "amount": 9225,
  "currency": "AED",
  "paid_at": "2026-03-23T10:10:00",
  "gateway": "stripe"
}
```
**`status` values:** `succeeded`, `pending`, `failed`, `cancelled`.

---

### Mark Token Used *(Payment UI Use)*
`POST /payments/mark-token-used`  
Invalidates the payment token after successful completion.
```bash
curl -X POST https://api.vouchergalaxy.com/payments/mark-token-used \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJ..."}'
```
**Response** `200`: `{"status": "success", "message": "Token marked as used"}`

---

## External Payment API

Allows external systems to generate payment links for users without going through the full app flow. All requests must be **HMAC-SHA256 signed**.

**Authentication:** Include `X-Signature: <hmac_sha256_hex>` header. The signature is computed as:
```
HMAC-SHA256(request_body_bytes, EXTERNAL_API_SECRET)
```
**Base path:** `/api/v1/external/`  
**Rate limit:** 60 requests/min

---

### Create Payment Link
`POST /api/v1/external/payment-link`
```bash
curl -X POST https://api.vouchergalaxy.com/api/v1/external/payment-link \
  -H "Content-Type: application/json" \
  -H "X-Signature: <hmac_signature>" \
  -d '{
    "phone_number": "+971501234567",
    "amount": 100.50,
    "currency": "AED",
    "first_name": "John",
    "second_name": "Doe",
    "reference_id": "EXT-REF-001",
    "return_url": "https://yourapp.com/payment-return",
    "webhook_url": "https://yourapp.com/webhooks/payment"
  }'
```
**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | string | ✅ | User's phone with country code (e.g. `+971...`) |
| `amount` | decimal | ✅ | Amount in standard currency unit (e.g. `100.50`) |
| `currency` | string | ✅ | 3-letter currency code (e.g. `USD`, `AED`) |
| `first_name` | string | — | User's first name |
| `second_name` | string | — | User's last name |
| `reference_id` | string | — | Your system's reference ID for reconciliation |
| `return_url` | URL | — | Redirect URL after payment |
| `webhook_url` | URL | — | Server webhook for payment notifications |

**Response** `200`:
```json
{
  "payment_url": "https://payment.vouchergalaxy.com/pay?token=eyJ...",
  "order_id": "uuid",
  "user_status": "existing",
  "amount": 100.50,
  "currency": "AED"
}
```
**`user_status`:** `existing` (user found by phone) or `created` (new user auto-created).

---

### Check Payment Status *(External)*
`POST /api/v1/external/payment-status`
```bash
curl -X POST https://api.vouchergalaxy.com/api/v1/external/payment-status \
  -H "Content-Type: application/json" \
  -H "X-Signature: <hmac_signature>" \
  -d '{"reference_id": "EXT-REF-001"}'
```
**Response** `200`:
```json
{
  "reference_id": "EXT-REF-001",
  "status": "succeeded",
  "amount": 100.50,
  "currency": "AED",
  "created_at": "2026-03-23T10:00:00",
  "order_id": "uuid"
}
```

---

## Admin

All admin endpoints require `Authorization: Bearer ADMIN_TOKEN` (role = `ADMIN`).  
**Rate Limit:** 30 requests/min on most endpoints.

### Dashboard Stats
`GET /admin/dashboard`
```bash
curl "https://api.vouchergalaxy.com/admin/dashboard?refresh=false" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Params:** `refresh` (bool, default: false) — force bypass cache (cached 60s).  
**Response** `200`:
```json
{
  "total_users": 500,
  "total_coupons": 120,
  "total_orders": 250,
  "total_revenue": 1050.0,
  "performance": {
    "views": [{"date": "2026-03-01", "count": 15}],
    "sold":  [{"date": "2026-03-01", "count": 3}]
  }
}
```

---

### List Users *(Admin)*
`GET /admin/users`
```bash
curl "https://api.vouchergalaxy.com/admin/users?skip=0&limit=20&active_only=false&search=john" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Params:** `skip`, `limit`, `active_only` (default: false), `search` (name or phone)  
**Response** `200`: `{"total": 500, "items": [...], "skip": 0, "limit": 20}`

---

### Get User by ID *(Admin)*
`GET /admin/users/{user_id}`
```bash
curl "https://api.vouchergalaxy.com/admin/users/{user_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### Toggle User Active Status *(Admin)*
`PATCH /admin/users/{user_id}/status`
```bash
curl -X PATCH "https://api.vouchergalaxy.com/admin/users/{user_id}/status?is_active=false" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Param:** `is_active` (bool, required).  
**Response** `200`: `{"message": "User deactivated successfully"}`

---

### Promote User to Admin *(Admin)*
`POST /admin/users/{user_id}/promote`
```bash
curl -X POST "https://api.vouchergalaxy.com/admin/users/{user_id}/promote" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`: `{"message": "User promoted to ADMIN successfully"}`

---

### Demote Admin to User *(Admin)*
`POST /admin/users/{user_id}/demote`
```bash
curl -X POST "https://api.vouchergalaxy.com/admin/users/{user_id}/demote" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`: `{"message": "Admin demoted to USER successfully"}`  
**Error:** `400` if trying to demote yourself.

---

### List Orders *(Admin)*
`GET /admin/orders`
```bash
curl "https://api.vouchergalaxy.com/admin/orders?skip=0&limit=20&status=paid&date_from=2026-01-01&date_to=2026-03-31" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `skip` | int | Pagination offset |
| `limit` | int | Max results 1–100 |
| `status` | string | Filter: `pending`, `paid`, `failed`, `cancelled` |
| `user_id` | UUID | Filter by user |
| `search` | string | Search by order ID, user phone, or name |
| `date_from` | string | ISO date (e.g. `2026-01-01`) |
| `date_to` | string | ISO date (e.g. `2026-12-31`) |

**Response** `200`: `{"total": 250, "items": [...], "skip": 0, "limit": 20}`

---

### Get Order by ID *(Admin)*
`GET /admin/orders/{order_id}`
```bash
curl "https://api.vouchergalaxy.com/admin/orders/{order_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### Coupon Analytics *(Admin)*
`GET /admin/analytics/coupons`
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/coupons?limit=20&sort_by=views&active_only=true&search=burger&category_id=UUID" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 20 | Max results 1–100 |
| `sort_by` | string | `views` | Sort: `views`, `redemptions`, `rate` |
| `active_only` | bool | false | Show active coupons only |
| `category_id` | UUID | — | Filter by category |
| `search` | string | — | Search by title, code, or brand |

---

### Coupon Analytics (Single) *(Admin)*
`GET /admin/analytics/coupons/{coupon_id}`
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/coupons/{coupon_id}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`: Detailed view breakdown, redemption counts, rate, trend data for that coupon.

---

### Quick Stats *(Admin)*
`GET /admin/analytics/quick-stats`  
Today's totals snapshot.
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/quick-stats" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`:
```json
{"today_views": 120, "today_redemptions": 15, "conversion_rate": 12.5}
```

---

### Trend Analysis *(Admin)*
`GET /admin/analytics/trends`
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/trends?days=30" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Param:** `days` (int, 7–90, default: 30)  
**Response** `200`: Daily views and redemptions for the date range.

---

### Category Performance *(Admin)*
`GET /admin/analytics/categories`
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/categories" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Response** `200`: Performance stats grouped by category (views, redemptions, revenue per category).

---

### Monthly Stats *(Admin)*
`GET /admin/analytics/monthly`
```bash
curl "https://api.vouchergalaxy.com/admin/analytics/monthly?months=12" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
**Query Param:** `months` (int, 1–24, default: 12)  
**Response** `200`: Monthly orders and revenue breakdown.

---

## Health

### Simple Health Check
`GET /`
```bash
curl https://api.vouchergalaxy.com/
```
**Response** `200`: `{"status": "OK", "version": "2.0.1"}`

---

### Detailed Health Check
`GET /health`
```bash
curl https://api.vouchergalaxy.com/health
```
**Response** `200`: `{"status": "OK", "database": "connected"}`  
**Degraded response**: `{"status": "degraded", "database": "error: ..."}`

---

## Discovery & Purchase Flows

### Flow 1: Browse by Category
```
GET  /categories/                         → list categories
GET  /categories/{slug}/coupons           → browse coupons
POST /cart/add                            → add to cart
POST /payments/init                       → initialize stripe payment
GET  /payments/status/{order_id}          → confirm payment
```

### Flow 2: Browse by Region / Country
```
GET  /regions/                            → list regions with countries
GET  /regions/{slug}/coupons  OR
GET  /countries/{slug}/coupons            → browse coupons
POST /cart/add  →  POST /payments/init
```

### Flow 3: Search & Filter Coupons
```
GET  /coupons/?search=burger&category_id=UUID&availability_type=local
POST /cart/add  →  GET /cart/  →  POST /payments/init
GET  /orders/                             → view order history
```

### Flow 4: Browse Packages (Bundles)
```
GET  /packages/?country=UAE&filter=highest_saving
GET  /packages/{package_id}              → view bundle details
POST /cart/add  (with package_id)
POST /payments/init  →  GET /payments/status/{order_id}
GET  /orders/{order_id}/invoice          → download invoice PDF
```

---

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request — invalid input or business logic failure |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found |
| 422 | Validation Error — request body schema mismatch |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error |

---

## Admin Credentials
`+917907975711` / `afsal@123`
