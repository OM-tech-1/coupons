# Manual cURL Commands for Package Creation

## Step 1: Login as Admin

```bash
curl -X POST "https://api.vouchergalaxy.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "country_code": "+91",
    "number": "8943657095",
    "password": "8943657095"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Copy the `access_token` value from the response!**

---

## Step 2: Create Package (Replace YOUR_TOKEN_HERE)

```bash
curl -X POST "https://api.vouchergalaxy.com/packages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Test Bundle - Nike Sports Pack",
    "slug": "test-nike-sports-pack",
    "description": "Amazing test bundle with multiple sports coupons",
    "picture_url": "https://example.com/nike-bundle.jpg",
    "brand": "Nike",
    "brand_url": "https://nike.com",
    "discount": 25.5,
    "category_id": "c1cf11f3-a5fb-4c75-827b-2aa2287e6b4d",
    "is_active": true,
    "is_featured": false,
    "expiration_date": "2025-12-31",
    "country": "UAE",
    "coupon_ids": []
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Test Bundle - Nike Sports Pack",
  "slug": "test-nike-sports-pack",
  "description": "Amazing test bundle with multiple sports coupons",
  "picture_url": "https://example.com/nike-bundle.jpg",
  "brand": "Nike",
  "brand_url": "https://nike.com",
  "discount": 25.5,
  "category_id": "c1cf11f3-a5fb-4c75-827b-2aa2287e6b4d",
  "country": "UAE",
  "is_active": true,
  "is_featured": false,
  "expiration_date": "2025-12-31",
  "created_at": "2024-03-10T10:30:00Z",
  "avg_rating": 0.0,
  "total_sold": 0,
  "pricing": {...},
  "final_prices": {...},
  "coupon_count": 0
}
```

---

## Step 3: Verify Package (Replace PACKAGE_ID)

```bash
curl -X GET "https://api.vouchergalaxy.com/packages/PACKAGE_ID"
```

---

## Complete One-Liner (Automated)

This command does everything in one go:

```bash
TOKEN=$(curl -s -X POST "https://api.vouchergalaxy.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "country_code": "+91",
    "number": "8943657095",
    "password": "8943657095"
  }' \
  | jq -r '.access_token') && \
echo "Token: $TOKEN" && \
curl -X POST "https://api.vouchergalaxy.com/packages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Bundle - Nike Sports Pack",
    "slug": "test-nike-sports-pack-'$(date +%s)'",
    "description": "Amazing test bundle with multiple sports coupons",
    "picture_url": "https://example.com/nike-bundle.jpg",
    "brand": "Nike",
    "brand_url": "https://nike.com",
    "discount": 25.5,
    "category_id": "c1cf11f3-a5fb-4c75-827b-2aa2287e6b4d",
    "is_active": true,
    "is_featured": false,
    "expiration_date": "2025-12-31",
    "country": "UAE",
    "coupon_ids": []
  }' | jq '.'
```

Note: The slug includes a timestamp to make it unique each time.

---

## Troubleshooting

### If you get 401 Unauthorized:
- Token expired or invalid
- Re-run Step 1 to get a new token

### If you get 403 Forbidden:
- User is not an admin
- Check user role in database

### If you get 422 Validation Error:
- Check the category_id exists
- Verify all required fields are present
- Check date format (YYYY-MM-DD)

### If you get a list of packages instead:
- You're hitting GET /packages instead of POST
- Make sure you're using `-X POST`
- Verify the Authorization header is included

---

## Using with Real Coupon IDs

To create a package with actual coupons, first get some coupon IDs:

```bash
curl -X GET "https://api.vouchergalaxy.com/coupons?limit=5" | jq '.[] | {id, name}'
```

Then use those IDs in the `coupon_ids` array:

```bash
curl -X POST "https://api.vouchergalaxy.com/packages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Real Bundle with Coupons",
    "slug": "real-bundle-'$(date +%s)'",
    "description": "Bundle with real coupons",
    "brand": "Nike",
    "discount": 20.0,
    "category_id": "c1cf11f3-a5fb-4c75-827b-2aa2287e6b4d",
    "is_active": true,
    "country": "UAE",
    "coupon_ids": [
      "39f2fe85-4d4a-4f24-ba64-3615237f09cb",
      "49d304d0-fcce-46a6-80e8-0e1dd2a41d3b"
    ]
  }' | jq '.'
```
