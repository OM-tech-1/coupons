-- Migration: 003_stripe_payment_integration.sql
-- Description: Add Stripe payment integration tables and columns
-- Created: 2026-02-05

-- =====================================================
-- PHASE 1: Enhance payments table
-- =====================================================

ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255) UNIQUE;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_client_secret VARCHAR(255);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS gateway VARCHAR(50) DEFAULT 'stripe';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_metadata JSONB;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Ensure one payment per order
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_order_payment'
    ) THEN
        ALTER TABLE payments ADD CONSTRAINT unique_order_payment UNIQUE (order_id);
    END IF;
END $$;

-- =====================================================
-- PHASE 2: Enhance orders table
-- =====================================================

ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_state VARCHAR(20) DEFAULT 'awaiting_payment';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);

-- =====================================================
-- PHASE 3: Create payment tokens table
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(512) UNIQUE NOT NULL,
    order_id UUID NOT NULL,
    payment_intent_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE,
    site_origin VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_payment_token_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_payment_tokens_token ON payment_tokens(token);
CREATE INDEX IF NOT EXISTS idx_payment_tokens_expires ON payment_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_payment_tokens_order ON payment_tokens(order_id);

-- Index for Stripe payment intent lookup
CREATE INDEX IF NOT EXISTS idx_payments_stripe_pi ON payments(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_orders_stripe_pi ON orders(stripe_payment_intent_id);

-- =====================================================
-- PHASE 4: Create payment status enum type (optional)
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status_enum') THEN
        CREATE TYPE payment_status_enum AS ENUM (
            'initiated',
            'pending', 
            'processing',
            'succeeded',
            'failed',
            'cancelled',
            'refunded'
        );
    END IF;
END $$;
