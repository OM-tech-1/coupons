-- ========================================
-- Migration 005: Indexes for Admin Dashboard Analytics
-- ========================================
-- Purpose: Add optimized indexes for admin dashboard queries
-- DB: Supabase PostgreSQL
-- 
-- NOTE: No new tables required for Phase 1-3 features.
-- The admin APIs use existing tables with aggregation queries.
-- ========================================

-- ========================================
-- 1. INDEXES FOR DASHBOARD ANALYTICS
-- ========================================

-- Index for faster order revenue calculations
CREATE INDEX IF NOT EXISTS idx_orders_status_created 
ON orders(status, created_at);

-- Index for user stats aggregation
CREATE INDEX IF NOT EXISTS idx_orders_user_status 
ON orders(user_id, status);

-- Index for coupon search by title (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_coupons_title_lower 
ON coupons(LOWER(title));

-- Index for coupon search by brand (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_coupons_brand_lower 
ON coupons(LOWER(brand));

-- Index for faster user listing by creation date
CREATE INDEX IF NOT EXISTS idx_users_created_at 
ON users(created_at DESC);

-- Index for active users filter
CREATE INDEX IF NOT EXISTS idx_users_is_active 
ON users(is_active);

-- ========================================
-- 2. [OPTIONAL] COUPON VIEWS TRACKING TABLE
-- ========================================
-- Uncomment below if you want to implement Phase 4 coupon tracking

/*
CREATE TABLE IF NOT EXISTS coupon_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_id UUID NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_coupon_views_coupon_id 
ON coupon_views(coupon_id);

CREATE INDEX IF NOT EXISTS idx_coupon_views_viewed_at 
ON coupon_views(viewed_at);

COMMENT ON TABLE coupon_views IS 'Track coupon detail page views for analytics';
*/

-- ========================================
-- MIGRATION COMPLETE
-- ========================================
-- Run this migration on Supabase SQL Editor
