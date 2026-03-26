-- Add used_at column to track when a coupon is redeemed/used by the user
ALTER TABLE user_coupons ADD COLUMN used_at TIMESTAMP NULL;

-- Add index for efficient filtering by used status
CREATE INDEX idx_user_coupons_used_at ON user_coupons(used_at);
