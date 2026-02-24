-- Add currency column to orders table
-- This stores the currency used when the order was placed

ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD' NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN orders.currency IS 'Currency code used for this order (USD, INR, AED, SAR, OMR, etc.)';

-- Update existing orders to have USD as default
UPDATE orders SET currency = 'USD' WHERE currency IS NULL;
