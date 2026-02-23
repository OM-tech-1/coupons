-- SQL queries to check webhook status directly in database
-- Run these in your database client (DBeaver, pgAdmin, sqlite3, etc.)

-- ============================================
-- 1. CHECK RECENT PAYMENTS
-- ============================================
-- Shows payment status changes from webhook
SELECT 
    id,
    stripe_payment_intent_id,
    status,                    -- Should change from 'pending' to 'succeeded'
    amount,
    currency,
    created_at,
    completed_at,              -- Gets set when webhook processes
    payment_metadata           -- Contains webhook event ID
FROM payments
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- 2. CHECK SPECIFIC PAYMENT BY STRIPE ID
-- ============================================
-- Replace 'pi_xxxxx' with your PaymentIntent ID
SELECT 
    id,
    order_id,
    stripe_payment_intent_id,
    status,
    amount,
    currency,
    created_at,
    completed_at,
    payment_metadata
FROM payments
WHERE stripe_payment_intent_id = 'pi_xxxxx';

-- ============================================
-- 3. CHECK ORDERS WITH PAYMENT STATUS
-- ============================================
-- Shows order status changes from webhook
SELECT 
    o.id,
    o.user_id,
    o.status,                  -- Should change from 'pending_payment' to 'paid'
    o.payment_state,           -- Should change to 'payment_completed'
    o.total_amount,
    o.payment_method,
    o.created_at,
    p.stripe_payment_intent_id,
    p.status as payment_status,
    p.completed_at as payment_completed_at
FROM orders o
LEFT JOIN payments p ON p.order_id = o.id
ORDER BY o.created_at DESC
LIMIT 10;

-- ============================================
-- 4. CHECK PENDING PAYMENTS (WEBHOOK NOT RECEIVED)
-- ============================================
-- These are payments waiting for webhook
SELECT 
    p.id,
    p.stripe_payment_intent_id,
    p.status,
    p.created_at,
    o.id as order_id,
    o.status as order_status,
    ROUND((julianday('now') - julianday(p.created_at)) * 24 * 60, 2) as minutes_pending
FROM payments p
LEFT JOIN orders o ON o.id = p.order_id
WHERE p.status = 'pending'
ORDER BY p.created_at DESC;

-- ============================================
-- 5. CHECK USER COUPONS (ADDED BY WEBHOOK)
-- ============================================
-- Shows coupons added to wallet after payment success
SELECT 
    uc.id,
    uc.user_id,
    uc.coupon_id,
    uc.claimed_at,             -- When coupon was added to wallet
    c.code,
    c.title,
    o.id as order_id,
    o.status as order_status,
    p.status as payment_status
FROM user_coupons uc
JOIN coupons c ON c.id = uc.coupon_id
LEFT JOIN orders o ON o.user_id = uc.user_id
LEFT JOIN order_items oi ON oi.order_id = o.id AND oi.coupon_id = uc.coupon_id
LEFT JOIN payments p ON p.order_id = o.id
ORDER BY uc.claimed_at DESC
LIMIT 20;

-- ============================================
-- 6. CHECK WEBHOOK METADATA
-- ============================================
-- Shows which payments were updated by webhook
SELECT 
    id,
    stripe_payment_intent_id,
    status,
    json_extract(payment_metadata, '$.stripe_event_id') as webhook_event_id,
    json_extract(payment_metadata, '$.failure_reason') as failure_reason,
    completed_at
FROM payments
WHERE payment_metadata IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- 7. COMPARE BEFORE/AFTER WEBHOOK
-- ============================================
-- Shows payments that changed status (webhook worked)
SELECT 
    id,
    stripe_payment_intent_id,
    status,
    created_at,
    completed_at,
    ROUND((julianday(completed_at) - julianday(created_at)) * 24 * 60, 2) as processing_minutes
FROM payments
WHERE status IN ('succeeded', 'failed', 'cancelled')
  AND completed_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- 8. CHECK ORDERS WITHOUT COUPONS (WEBHOOK FAILED)
-- ============================================
-- Orders marked as paid but no coupons in wallet (shouldn't happen)
SELECT 
    o.id,
    o.user_id,
    o.status,
    o.total_amount,
    o.created_at,
    COUNT(uc.id) as coupons_in_wallet
FROM orders o
LEFT JOIN user_coupons uc ON uc.user_id = o.user_id
WHERE o.status = 'paid'
GROUP BY o.id, o.user_id, o.status, o.total_amount, o.created_at
HAVING COUNT(uc.id) = 0
ORDER BY o.created_at DESC;

-- ============================================
-- 9. SUMMARY STATISTICS
-- ============================================
SELECT 
    'Total Payments' as metric,
    COUNT(*) as count
FROM payments
UNION ALL
SELECT 
    'Pending Payments',
    COUNT(*)
FROM payments
WHERE status = 'pending'
UNION ALL
SELECT 
    'Succeeded Payments',
    COUNT(*)
FROM payments
WHERE status = 'succeeded'
UNION ALL
SELECT 
    'Failed Payments',
    COUNT(*)
FROM payments
WHERE status = 'failed'
UNION ALL
SELECT 
    'Orders Paid',
    COUNT(*)
FROM orders
WHERE status = 'paid'
UNION ALL
SELECT 
    'Orders Pending Payment',
    COUNT(*)
FROM orders
WHERE status = 'pending_payment';
