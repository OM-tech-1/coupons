-- Migration: Add index on payments.order_id for faster payment lookups
-- Description: Improves /payments/init performance by 50-150ms

-- Add index for faster payment lookup by order_id
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
