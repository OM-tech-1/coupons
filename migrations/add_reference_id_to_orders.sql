ALTER TABLE orders ADD COLUMN reference_id VARCHAR(255);
CREATE UNIQUE INDEX ix_orders_reference_id ON orders (reference_id);
