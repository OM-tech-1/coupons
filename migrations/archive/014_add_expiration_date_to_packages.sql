-- Add expiration_date column to packages table
-- This allows packages to have an expiration date similar to coupons

ALTER TABLE packages 
ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP NULL;

-- Add comment for documentation
COMMENT ON COLUMN packages.expiration_date IS 'Optional expiration date for the package';
