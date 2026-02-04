# Coupon App API Documentation

**Base URL:** `http://156.67.216.229`  
**Swagger UI:** http://156.67.216.229/docs

---

## Authentication

### Register
```bash
curl -X POST http://156.67.216.229/auth/register \
  -H "Content-Type: application/json" \
  -d '{"country_code":"+91","number":"9876543210","password":"pass123","full_name":"Test User"}'
```

### Login
```bash
curl -X POST http://156.67.216.229/auth/login \
  -H "Content-Type: application/json" \
  -d '{"country_code":"+91","number":"7907975711","password":"afsal@123"}'
```

---

## User Profile

### Get Profile
```bash
curl http://156.67.216.229/user/me -H "Authorization: Bearer TOKEN"
```

### Update Profile (Password Required)
```bash
curl -X PUT http://156.67.216.229/user/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"current_password":"afsal@123","full_name":"New Name","email":"email@example.com"}'
```

### Get Claimed Coupons (with revealed codes)
```bash
curl http://156.67.216.229/user/coupons -H "Authorization: Bearer TOKEN"
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

## Coupons

### List Coupons
```bash
curl "http://156.67.216.229/coupons/?skip=0&limit=10&active_only=true"
```

### Create Coupon (Admin)
```bash
curl -X POST http://156.67.216.229/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "code": "MCDEAL50",
    "redeem_code": "ABC123XYZ",
    "brand": "McDonalds",
    "title": "50% off any meal",
    "discount_type": "percentage",
    "discount_amount": 50.0,
    "price": 4.99
  }'
```

### Update/Delete Coupon (Admin)
```bash
curl -X PUT http://156.67.216.229/coupons/{id} -H "Authorization: Bearer TOKEN" \
  -d '{"redeem_code":"NEWCODE456","price":5.99}'
curl -X DELETE http://156.67.216.229/coupons/{id} -H "Authorization: Bearer TOKEN"
```

---

## Cart

### Add to Cart
```bash
curl -X POST http://156.67.216.229/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"coupon_id":"uuid-here","quantity":1}'
```

### View Cart
```bash
curl http://156.67.216.229/cart/ -H "Authorization: Bearer TOKEN"
```
**Response:**
```json
{"items":[...],"total_items":1,"total_amount":9.99}
```

### Remove from Cart
```bash
curl -X DELETE http://156.67.216.229/cart/{coupon_id} -H "Authorization: Bearer TOKEN"
```

### Clear Cart
```bash
curl -X DELETE http://156.67.216.229/cart/ -H "Authorization: Bearer TOKEN"
```

---

## Orders

### Checkout (Mock Payment)
```bash
curl -X POST http://156.67.216.229/orders/checkout \
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
curl http://156.67.216.229/orders/ -H "Authorization: Bearer TOKEN"
```

### Get Order by ID
```bash
curl http://156.67.216.229/orders/{order_id} -H "Authorization: Bearer TOKEN"
```

---

## Purchase Flow
```
1. Browse coupons     GET  /coupons/
2. Add to cart        POST /cart/add
3. View cart          GET  /cart/
4. Checkout           POST /orders/checkout
5. View orders        GET  /orders/
```

---

## Health

### Health Check (Simple)
```bash
curl http://156.67.216.229/
```
**Response:** `{"status":"OK"}`

### Health Check (Detailed)
```bash
curl http://156.67.216.229/health
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
