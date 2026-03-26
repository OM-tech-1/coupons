-- Database indexes for high-load performance optimization
-- Run this migration on your PostgreSQL database

-- User table indexes (for auth and profile lookups)
CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(country_code, phone_number);

-- Coupon table indexes (for listing and lookup)
CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code);
CREATE INDEX IF NOT EXISTS idx_coupons_is_active ON coupons(is_active);
CREATE INDEX IF NOT EXISTS idx_coupons_active_list ON coupons(is_active, created_at DESC);

-- Cart table indexes (for cart operations)
CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_coupon ON cart_items(user_id, coupon_id);

-- Order table indexes (for order history)
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);

-- Order items index
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

-- User coupons index (for claimed coupons lookup)
CREATE INDEX IF NOT EXISTS idx_user_coupons_user_id ON user_coupons(user_id);
CREATE INDEX IF NOT EXISTS idx_user_coupons_composite ON user_coupons(user_id, coupon_id);
