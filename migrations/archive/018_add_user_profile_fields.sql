-- Migration: Add user profile fields and OTP support
-- This adds email, profile information, address fields, and OTP for password reset

-- ========================================
-- 1. ADD EMAIL AND OTP FIELDS
-- ========================================

-- Add email field (unique, indexed)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Add OTP fields for password reset
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS otp VARCHAR(10);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS otp_expiry TIMESTAMP;

-- ========================================
-- 2. ADD PROFILE FIELDS
-- ========================================

-- Personal information
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS date_of_birth DATE;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS gender VARCHAR(20);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS country_of_residence VARCHAR(100);

-- ========================================
-- 3. ADD ADDRESS FIELDS
-- ========================================

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS home_address VARCHAR(255);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS town VARCHAR(100);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS state_province VARCHAR(100);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS address_country VARCHAR(100);

-- ========================================
-- 4. ADD COMMENTS FOR DOCUMENTATION
-- ========================================

COMMENT ON COLUMN users.email IS 'User email address for notifications and password reset';
COMMENT ON COLUMN users.otp IS 'One-time password for password reset verification';
COMMENT ON COLUMN users.otp_expiry IS 'Expiration timestamp for OTP';
COMMENT ON COLUMN users.date_of_birth IS 'User date of birth';
COMMENT ON COLUMN users.gender IS 'User gender (Male, Female, Other)';
COMMENT ON COLUMN users.country_of_residence IS 'Country where user resides';
COMMENT ON COLUMN users.home_address IS 'User home address line';
COMMENT ON COLUMN users.town IS 'User town/city';
COMMENT ON COLUMN users.state_province IS 'User state or province';
COMMENT ON COLUMN users.postal_code IS 'User postal/ZIP code';
COMMENT ON COLUMN users.address_country IS 'Country for user address';

-- ========================================
-- MIGRATION COMPLETE
-- ========================================
