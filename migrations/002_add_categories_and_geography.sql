-- Migration: Add categories and geography structure
-- Run this migration on your PostgreSQL database

-- ========================================
-- 1. CREATE CATEGORIES TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_is_active ON categories(is_active);

-- ========================================
-- 2. CREATE REGIONS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_regions_name ON regions(name);
CREATE INDEX IF NOT EXISTS idx_regions_slug ON regions(slug);
CREATE INDEX IF NOT EXISTS idx_regions_is_active ON regions(is_active);

-- ========================================
-- 3. CREATE COUNTRIES TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS countries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    country_code VARCHAR(2) UNIQUE NOT NULL,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_countries_name ON countries(name);
CREATE INDEX IF NOT EXISTS idx_countries_slug ON countries(slug);
CREATE INDEX IF NOT EXISTS idx_countries_country_code ON countries(country_code);
CREATE INDEX IF NOT EXISTS idx_countries_region_id ON countries(region_id);
CREATE INDEX IF NOT EXISTS idx_countries_is_active ON countries(is_active);

-- ========================================
-- 4. CREATE COUPON_COUNTRIES JOIN TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS coupon_countries (
    coupon_id UUID NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    country_id UUID NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (coupon_id, country_id),
    CONSTRAINT uq_coupon_country UNIQUE (coupon_id, country_id)
);

CREATE INDEX IF NOT EXISTS idx_coupon_countries_coupon_id ON coupon_countries(coupon_id);
CREATE INDEX IF NOT EXISTS idx_coupon_countries_country_id ON coupon_countries(country_id);

-- ========================================
-- 5. ADD NEW COLUMNS TO COUPONS TABLE
-- ========================================
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES categories(id) ON DELETE SET NULL;
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS availability_type VARCHAR(20) DEFAULT 'online';

CREATE INDEX IF NOT EXISTS idx_coupons_category_id ON coupons(category_id);
CREATE INDEX IF NOT EXISTS idx_coupons_availability_type ON coupons(availability_type);

-- ========================================
-- 6. SEED INITIAL DATA - CATEGORIES
-- ========================================
INSERT INTO categories (name, slug, description, icon, display_order, is_active) VALUES
('Pets & Pet Supplies', 'pets-pet-supplies', 'Pet food, toys, grooming products, accessories, and pet health items', '🐾', 1, TRUE),
('Automotive & Car Care', 'automotive-car-care', 'Car cleaning, detailing, spare parts, repairs, tires, and accessories', '🚗', 2, TRUE),
('Home Furnishings & Decor', 'home-furnishings-decor', 'Furniture, sofas, beds, pillows, bedding, rugs, and lighting', '🏠', 3, TRUE),
('Electronics & Gadgets', 'electronics-gadgets', 'Smartphones, laptops, accessories, audio devices, and smart home products', '📱', 4, TRUE),
('Fashion & Apparel', 'fashion-apparel', 'Clothing, shoes, bags, and accessories for men, women, and children', '👗', 5, TRUE),
('Beauty & Personal Care', 'beauty-personal-care', 'Skincare, cosmetics, hair care, grooming, and hygiene products', '💄', 6, TRUE),
('Food & Grocery', 'food-grocery', 'Online grocery shopping, meal kits, snacks, and specialty foods', '🛒', 7, TRUE),
('Health & Wellness', 'health-wellness', 'Vitamins, supplements, fitness products, and wellness services', '🏃', 8, TRUE),
('Tools & DIY', 'tools-diy', 'Hand tools, power tools, workshop equipment, and DIY supplies', '🔧', 9, TRUE),
('Travel & Experiences', 'travel-experiences', 'Hotels, flights, car rentals, tours, and experience bookings', '✈️', 10, TRUE)
ON CONFLICT (slug) DO NOTHING;

-- ========================================
-- 7. SEED INITIAL DATA - REGIONS
-- ========================================
INSERT INTO regions (name, slug, description, display_order, is_active) VALUES
('Asia', 'asia', 'Countries in the Asian continent', 1, TRUE),
('Middle East', 'middle-east', 'Countries in the Middle East region', 2, TRUE),
('Europe', 'europe', 'Countries in the European continent', 3, TRUE),
('North America', 'north-america', 'Countries in North America', 4, TRUE),
('South America', 'south-america', 'Countries in South America', 5, TRUE),
('Africa', 'africa', 'Countries in the African continent', 6, TRUE)
ON CONFLICT (slug) DO NOTHING;

-- ========================================
-- 8. SEED INITIAL DATA - COUNTRIES
-- ========================================
-- Asia
INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'India', 'india', 'IN', r.id, TRUE FROM regions r WHERE r.slug = 'asia'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Thailand', 'thailand', 'TH', r.id, TRUE FROM regions r WHERE r.slug = 'asia'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Philippines', 'philippines', 'PH', r.id, TRUE FROM regions r WHERE r.slug = 'asia'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Indonesia', 'indonesia', 'ID', r.id, TRUE FROM regions r WHERE r.slug = 'asia'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Malaysia', 'malaysia', 'MY', r.id, TRUE FROM regions r WHERE r.slug = 'asia'
ON CONFLICT (country_code) DO NOTHING;

-- Middle East
INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'United Arab Emirates', 'united-arab-emirates', 'AE', r.id, TRUE FROM regions r WHERE r.slug = 'middle-east'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Saudi Arabia', 'saudi-arabia', 'SA', r.id, TRUE FROM regions r WHERE r.slug = 'middle-east'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Oman', 'oman', 'OM', r.id, TRUE FROM regions r WHERE r.slug = 'middle-east'
ON CONFLICT (country_code) DO NOTHING;

-- Europe
INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'Germany', 'germany', 'DE', r.id, TRUE FROM regions r WHERE r.slug = 'europe'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'United Kingdom', 'united-kingdom', 'GB', r.id, TRUE FROM regions r WHERE r.slug = 'europe'
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO countries (name, slug, country_code, region_id, is_active)
SELECT 'France', 'france', 'FR', r.id, TRUE FROM regions r WHERE r.slug = 'europe'
ON CONFLICT (country_code) DO NOTHING;

-- ========================================
-- MIGRATION COMPLETE
-- ========================================
