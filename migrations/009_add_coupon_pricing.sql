-- Add pricing column to coupons table for multi-currency support
ALTER TABLE coupons ADD COLUMN pricing JSONB DEFAULT NULL;
