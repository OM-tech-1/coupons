-- ========================================
-- Migration 006: Add Stock and Featured Fields to Coupons
-- ========================================
-- Purpose: Add stock and is_featured columns to coupons table
-- DB: Supabase PostgreSQL
-- ========================================

-- Add stock column (nullable integer for available stock)
ALTER TABLE coupons 
ADD COLUMN IF NOT EXISTS stock INTEGER DEFAULT NULL;

COMMENT ON COLUMN coupons.stock IS 'Available stock count. NULL means unlimited.';

-- Add is_featured column (boolean for homepage display)
ALTER TABLE coupons 
ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN coupons.is_featured IS 'Featured coupons display on homepage';

-- Create index for featured coupons (fast filtering)
CREATE INDEX IF NOT EXISTS idx_coupons_is_featured 
ON coupons(is_featured) 
WHERE is_featured = TRUE;

-- Create index for user search by name (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_users_full_name_lower 
ON users(LOWER(full_name));

-- ========================================
-- MIGRATION COMPLETE
-- ========================================
-- Run this migration on Supabase SQL Editor
