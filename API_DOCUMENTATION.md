# Coupon App API Documentation

**Base URL:** `https://api.vouchergalaxy.com`  
**Swagger UI:** https://api.vouchergalaxy.com/docs

---

## Authentication

### Register
```bash
curl -X POST https://api.vouchergalaxy.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"country_code":"+91","number":"9876543210","password":"pass123","full_name":"Test User"}'
```

### Login
```bash
curl -X POST https://api.vouchergalaxy.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"country_code":"+91","number":"7907975711","password":"afsal@123"}'
```

---

## User Profile

### Get Profile
```bash
curl https://api.vouchergalaxy.com/user/me -H "Authorization: Bearer TOKEN"
```

### Update Profile (Password Required)
```bash
curl -X PUT https://api.vouchergalaxy.com/user/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"current_password":"afsal@123","full_name":"New Name","email":"email@example.com"}'
```

### Get Claimed Coupons (with revealed codes)
```bash
curl https://api.vouchergalaxy.com/user/coupons -H "Authorization: Bearer TOKEN"
```
**Response (redeem_code is revealed after purchase):**
```json
[
  {
    "id": "uuid",
    "coupon_id": "uuid",
    "claimed_at": "2026-02-04T12:00:00",
    "coupon": {
      "code": "MCDEAL50",
      "redeem_code": "ABC123XYZ",
      "brand": "McDonald's",
      "title": "50% off any meal",
      "discount_amount": 50.0
    }
  }
]
```

---

## Categories

### List All Categories
```bash
curl https://api.vouchergalaxy.com/categories/
```
**Response:** Returns 10 categories (Pets, Automotive, Electronics, Fashion, Beauty, Food & Grocery, Health, Tools, Travel, Home Furnishings)

### List Categories with Coupon Counts
```bash
curl https://api.vouchergalaxy.com/categories/with-counts
```

### Get Category by Slug
```bash
curl https://api.vouchergalaxy.com/categories/pets-pet-supplies
```

### Browse Coupons in Category
```bash
curl "https://api.vouchergalaxy.com/categories/electronics-gadgets/coupons?limit=20&active_only=true"
```

### Create Category (Admin)
```bash
curl -X POST https://api.vouchergalaxy.com/categories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "Sports & Fitness",
    "slug": "sports-fitness",
    "description": "Sports equipment and fitness products",
    "icon": "⚽",
    "display_order": 11
  }'
```

---

## Regions & Countries

### List All Regions with Countries
```bash
curl https://api.vouchergalaxy.com/regions/
```
**Response:** Returns regions (Asia, Middle East, Europe, etc.) with nested countries

### Get Region by Slug
```bash
curl https://api.vouchergalaxy.com/regions/asia
```

### Browse Coupons in Region
```bash
curl "https://api.vouchergalaxy.com/regions/middle-east/coupons?limit=20"
```

### List All Countries
```bash
curl https://api.vouchergalaxy.com/countries/
# Filter by region
curl "https://api.vouchergalaxy.com/countries/?region_id=REGION_UUID"
```

### Get Country by Slug
```bash
curl https://api.vouchergalaxy.com/countries/india
```

### Browse Coupons in Country
```bash
curl "https://api.vouchergalaxy.com/countries/united-arab-emirates/coupons?limit=20"
```

---

## Coupons

### List Coupons (Enhanced with Filters)
```bash
# Basic listing
curl "https://api.vouchergalaxy.com/coupons/?skip=0&limit=10&active_only=true"

# Filter by category
curl "https://api.vouchergalaxy.com/coupons/?category_id=CATEGORY_UUID&active_only=true"

# Filter by region
curl "https://api.vouchergalaxy.com/coupons/?region_id=REGION_UUID&active_only=true"

# Filter by country
curl "https://api.vouchergalaxy.com/coupons/?country_id=COUNTRY_UUID&active_only=true"

# Filter by availability type (online/local/both)
curl "https://api.vouchergalaxy.com/coupons/?availability_type=local&active_only=true"

# Combine filters: Electronics coupons in India
curl "https://api.vouchergalaxy.com/coupons/?category_id=CATEGORY_UUID&country_id=COUNTRY_UUID&active_only=true"
```

### Create Coupon (Admin) - With Category & Geography
```bash
curl -X POST https://api.vouchergalaxy.com/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "code": "PETLOVE50",
    "redeem_code": "ABC123XYZ",
    "brand": "PetStore",
    "title": "50% off pet food",
    "discount_type": "percentage",
    "discount_amount": 50.0,
    "price": 2.99,
    "category_id": "CATEGORY_UUID",
    "availability_type": "local",
    "country_ids": ["COUNTRY_UUID_1", "COUNTRY_UUID_2"]
  }'
```

### Update/Delete Coupon (Admin)
```bash
curl -X PUT https://api.vouchergalaxy.com/coupons/{id} -H "Authorization: Bearer TOKEN" \
  -d '{"redeem_code":"NEWCODE456","price":5.99,"category_id":"CATEGORY_UUID"}'
curl -X DELETE https://api.vouchergalaxy.com/coupons/{id} -H "Authorization: Bearer TOKEN"
```

---

## Cart

### Add to Cart
```bash
curl -X POST https://api.vouchergalaxy.com/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"coupon_id":"uuid-here","quantity":1}'
```

### View Cart
```bash
curl https://api.vouchergalaxy.com/cart/ -H "Authorization: Bearer TOKEN"
```
**Response:**
```json
{"items":[...],"total_items":1,"total_amount":9.99}
```

### Remove from Cart
```bash
curl -X DELETE https://api.vouchergalaxy.com/cart/{coupon_id} -H "Authorization: Bearer TOKEN"
```

### Clear Cart
```bash
curl -X DELETE https://api.vouchergalaxy.com/cart/ -H "Authorization: Bearer TOKEN"
```

---

## Orders

### Checkout (Mock Payment)
```bash
curl -X POST https://api.vouchergalaxy.com/orders/checkout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"payment_method":"mock"}'
```
**Response:**
```json
{"id":"uuid","status":"paid","total_amount":9.99,"payment_method":"mock","items":[...]}
```

### Get Orders
```bash
curl https://api.vouchergalaxy.com/orders/ -H "Authorization: Bearer TOKEN"
```

### Get Order by ID
```bash
curl https://api.vouchergalaxy.com/orders/{order_id} -H "Authorization: Bearer TOKEN"
```

---

## Discovery & Purchase Flow

### Option 1: Browse by Category
```
1. List categories           GET  /categories/
2. Browse category coupons   GET  /categories/{slug}/coupons
3. Add to cart               POST /cart/add
4. Checkout                  POST /orders/checkout
```

### Option 2: Browse by Region/Country
```
1. List regions              GET  /regions/
2. Browse region coupons     GET  /regions/{slug}/coupons
   OR browse country coupons GET  /countries/{slug}/coupons
3. Add to cart               POST /cart/add
4. Checkout                  POST /orders/checkout
```

### Option 3: Advanced Filtering
```
1. Filter coupons            GET  /coupons/?category_id=UUID&country_id=UUID&availability_type=local
2. Add to cart               POST /cart/add
3. View cart                 GET  /cart/
4. Checkout                  POST /orders/checkout
5. View orders               GET  /orders/
```

---

## Health

### Health Check (Simple)
```bash
curl https://api.vouchergalaxy.com/
```
**Response:** `{"status":"OK"}`

### Health Check (Detailed)
```bash
curl https://api.vouchergalaxy.com/health
```
**Response:** `{"status":"OK","database":"connected"}`

---

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |

---

## Admin: +917907975711 / afsal@123

---

## Stripe Payments

### Initialize Payment
Creates a Stripe PaymentIntent and returns a temporary token for the payment UI.
```bash
curl -X POST https://api.vouchergalaxy.com/payments/init \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"order_id":"ORDER_UUID", "amount": 1000, "currency": "USD"}'
```
**Response:**
```json
{
  "redirect_url": "https://payment.vouchergalaxy.com/pay?token=...",
  "token": "eyJ...",
  "expires_at": "2026-02-06T12:00:00",
  "order_id": "uuid",
  "payment_intent_id": "pi_..."
}
```

### Validate Token
Used by the Frontend UI to validate the token and get the Client Secret.
```bash
curl -X POST https://api.vouchergalaxy.com/payments/validate-token \
  -H "Content-Type: application/json" \
  -d '{"token":"JWT_TOKEN"}'
```
**Response:**
```json
{
  "client_secret": "pi_...",
  "publishable_key": "pk_test_...",
  "amount": 1000,
  "currency": "USD",
  "order_id": "uuid",
  "return_url": "https://callback.com"
}
```

### Get Payment Status
Check the status of a payment by Order ID.
```bash
curl https://api.vouchergalaxy.com/payments/status/{order_id} -H "Authorization: Bearer TOKEN"
```
**Response:** `{"status": "succeeded", "amount": 1000, "gateway": "stripe", ...}`

### Mark Token Used
Invalidates the token after successful payment to prevent reuse.
```bash
curl -X POST https://api.vouchergalaxy.com/payments/mark-token-used \
  -H "Content-Type: application/json" \
  -d '{"token":"JWT_TOKEN"}'
```

