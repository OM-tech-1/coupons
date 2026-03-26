ALTER TABLE order_items ALTER COLUMN coupon_id DROP NOT NULL;
ALTER TABLE order_items ADD COLUMN package_id UUID REFERENCES packages(id) NULL;
CREATE INDEX ix_order_items_package_id ON order_items(package_id);
