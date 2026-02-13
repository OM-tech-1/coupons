-- Featured Coupons Diagnostic Queries
-- Run these in your PostgreSQL database to diagnose the issue

-- 1. Check total coupons
SELECT COUNT(*) as total_coupons FROM coupons;

-- 2. Check how many coupons are featured (any status)
SELECT COUNT(*) as featured_count 
FROM coupons 
WHERE is_featured = true;

-- 3. Check how many coupons are active AND featured (what API returns)
SELECT COUNT(*) as active_featured_count 
FROM coupons 
WHERE is_featured = true AND is_active = true;

-- 4. Show details of ALL featured coupons
SELECT 
    code, 
    title, 
    is_featured, 
    is_active, 
    price,
    stock,
    created_at
FROM coupons
WHERE is_featured = true
ORDER BY created_at DESC;

-- 5. Show details of ACTIVE featured coupons (what API should return)
SELECT 
    code, 
    title, 
    is_featured, 
    is_active, 
    price,
    stock,
    created_at
FROM coupons
WHERE is_featured = true AND is_active = true
ORDER BY created_at DESC;

-- ============================================================
-- SOLUTION: Set some coupons as featured
-- ============================================================

-- Option A: Set first 5 active coupons as featured
UPDATE coupons 
SET is_featured = true 
WHERE id IN (
    SELECT id FROM coupons 
    WHERE is_active = true 
    ORDER BY created_at DESC 
    LIMIT 5
);

-- Option B: Set specific coupons by code
-- UPDATE coupons 
-- SET is_featured = true, is_active = true 
-- WHERE code IN ('YOUR_CODE_1', 'YOUR_CODE_2', 'YOUR_CODE_3');

-- Verify the update
SELECT code, title, is_featured, is_active 
FROM coupons 
WHERE is_featured = true;
