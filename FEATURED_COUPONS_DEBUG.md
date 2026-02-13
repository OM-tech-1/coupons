# Featured Coupons Debugging Guide

## Problem
The `/coupons/featured` endpoint returns an empty array even though you expect featured coupons to exist.

## Root Cause Analysis

### ✅ What We Checked
1. **Redis Connection**: Working perfectly
2. **Cache Layer**: Empty (no cached data)
3. **Code Logic**: Correct - queries for `is_featured=true AND is_active=true`

### ❌ The Issue
The database likely has **no coupons** that meet BOTH conditions:
- `is_featured = true`
- `is_active = true`

## Solution

### Option 1: Check Database (Recommended)

Run these SQL queries to diagnose:

```sql
-- Check total coupons
SELECT COUNT(*) as total_coupons FROM coupons;

-- Check featured coupons (any status)
SELECT COUNT(*) as featured_coupons 
FROM coupons 
WHERE is_featured = true;

-- Check active featured coupons (what the API returns)
SELECT COUNT(*) as active_featured 
FROM coupons 
WHERE is_featured = true AND is_active = true;

-- Show details of all featured coupons
SELECT code, title, is_featured, is_active, created_at
FROM coupons
WHERE is_featured = true
ORDER BY created_at DESC;
```

### Option 2: Set Coupons as Featured via API

Use the **Update Coupon** endpoint to mark coupons as featured:

```bash
# Get a coupon ID first
GET {{base_url}}/coupons/?limit=10

# Then update it to be featured
PUT {{base_url}}/coupons/{coupon_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "is_featured": true,
  "is_active": true
}
```

### Option 3: Update Database Directly

If you have database access:

```sql
-- Set specific coupons as featured
UPDATE coupons 
SET is_featured = true, is_active = true 
WHERE code IN ('SAVE20', 'DISCOUNT50', 'WELCOME10');

-- Or set the first 5 active coupons as featured
UPDATE coupons 
SET is_featured = true 
WHERE id IN (
    SELECT id FROM coupons 
    WHERE is_active = true 
    ORDER BY created_at DESC 
    LIMIT 5
);
```

## Verification Steps

After updating coupons:

1. **Clear cache** (already done by our script)
2. **Call the API**:
   ```bash
   GET {{base_url}}/coupons/featured?limit=10
   ```
3. **Should return** the featured coupons

## Quick Test

Try this endpoint to see ALL coupons (not just featured):
```bash
GET {{base_url}}/coupons/?limit=10
```

If this returns coupons, then the database connection is fine, and you just need to mark some as featured.

## Common Mistakes

❌ **Setting `is_featured=true` but `is_active=false`**
- The API filters for BOTH conditions
- Inactive coupons won't show in featured list

❌ **Expecting automatic featured coupons**
- Coupons are NOT automatically featured
- You must explicitly set `is_featured=true`

❌ **Cache not clearing**
- Cache TTL is 5 minutes (CACHE_TTL_MEDIUM)
- Wait 5 minutes or restart the server to clear cache
