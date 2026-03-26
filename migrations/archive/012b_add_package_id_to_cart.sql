-- Add package_id to cart_items so users can add packages to cart
ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS package_id UUID REFERENCES packages(id);
ALTER TABLE cart_items ALTER COLUMN coupon_id DROP NOT NULL;
