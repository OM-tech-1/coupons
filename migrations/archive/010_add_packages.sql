-- Migration 010: Add Packages Feature
-- Creates packages table, package_coupons association table,
-- and adds is_package_coupon flag to coupons table.

-- Packages table
CREATE TABLE IF NOT EXISTS packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(220) UNIQUE NOT NULL,
    description TEXT,
    picture_url VARCHAR(500),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_packages_slug ON packages(slug);
CREATE INDEX IF NOT EXISTS ix_packages_category ON packages(category_id);
CREATE INDEX IF NOT EXISTS ix_packages_active ON packages(is_active);
CREATE INDEX IF NOT EXISTS ix_packages_featured ON packages(is_featured) WHERE is_featured = TRUE;

-- Package-Coupon association table
CREATE TABLE IF NOT EXISTS package_coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    coupon_id UUID NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    UNIQUE(package_id, coupon_id)
);

CREATE INDEX IF NOT EXISTS ix_package_coupons_package ON package_coupons(package_id);
CREATE INDEX IF NOT EXISTS ix_package_coupons_coupon ON package_coupons(coupon_id);

-- Add is_package_coupon flag to coupons
ALTER TABLE coupons
ADD COLUMN IF NOT EXISTS is_package_coupon BOOLEAN DEFAULT FALSE;
