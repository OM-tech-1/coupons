"""Baseline migration – consolidates all 22 historical SQL files into one.

Revision ID: 0001
Revises: (none – first migration)
Create Date: 2026-03-26

Running `alembic upgrade head` on a **fresh** database builds the full schema.
Running it on an **existing** database that was already stamped via
`alembic stamp head` is a no-op (all statements are idempotent).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ──────────────────────────────────────────────────────────────
    # Helper – run a statement and silently ignore if it has no
    # effect (e.g. column already exists, index already exists).
    # Every statement here is safe to run multiple times.
    # ──────────────────────────────────────────────────────────────

    def run(sql: str) -> None:
        conn.execute(sa.text(sql))

    # ══════════════════════════════════════════════════════════════
    # CORE TABLES  (originally created by Base.metadata.create_all
    # before Alembic was introduced)
    # ══════════════════════════════════════════════════════════════

    run("""
        CREATE TABLE IF NOT EXISTS users (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            full_name   VARCHAR(100)  NOT NULL,
            country_code VARCHAR(5)   NOT NULL,
            phone_number VARCHAR(20)  NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role        VARCHAR(20)   NOT NULL DEFAULT 'USER',
            is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_users_phone UNIQUE (country_code, phone_number)
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS categories (
            id            UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
            name          VARCHAR(100) UNIQUE NOT NULL,
            slug          VARCHAR(120) UNIQUE NOT NULL,
            description   TEXT,
            icon          VARCHAR(50),
            display_order INTEGER  DEFAULT 0,
            is_active     BOOLEAN  DEFAULT TRUE,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS regions (
            id            UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
            name          VARCHAR(100) UNIQUE NOT NULL,
            slug          VARCHAR(120) UNIQUE NOT NULL,
            description   TEXT,
            display_order INTEGER  DEFAULT 0,
            is_active     BOOLEAN  DEFAULT TRUE,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS countries (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name         VARCHAR(100) NOT NULL,
            slug         VARCHAR(120) UNIQUE NOT NULL,
            country_code VARCHAR(2)   UNIQUE NOT NULL,
            region_id    UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
            is_active    BOOLEAN  DEFAULT TRUE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS coupons (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code            VARCHAR(50)  UNIQUE NOT NULL,
            title           VARCHAR(200) NOT NULL,
            description     TEXT,
            discount_type   VARCHAR(20)  NOT NULL,
            discount_amount FLOAT        NOT NULL,
            is_active       BOOLEAN  DEFAULT TRUE,
            is_deleted      BOOLEAN  DEFAULT FALSE,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS coupon_countries (
            coupon_id  UUID NOT NULL REFERENCES coupons(id)  ON DELETE CASCADE,
            country_id UUID NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (coupon_id, country_id),
            CONSTRAINT uq_coupon_country UNIQUE (coupon_id, country_id)
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS user_coupons (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
            coupon_id  UUID NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
            claimed_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT uq_user_coupon UNIQUE (user_id, coupon_id)
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id   UUID REFERENCES users(id)   ON DELETE CASCADE,
            coupon_id UUID REFERENCES coupons(id) ON DELETE CASCADE,
            quantity  INTEGER NOT NULL DEFAULT 1,
            added_at  TIMESTAMP DEFAULT NOW()
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS orders (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            total      FLOAT NOT NULL,
            status     VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS order_items (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id  UUID NOT NULL REFERENCES orders(id)  ON DELETE CASCADE,
            coupon_id UUID          REFERENCES coupons(id) ON DELETE SET NULL,
            quantity  INTEGER NOT NULL,
            price     FLOAT   NOT NULL
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS payments (
            id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            amount   FLOAT NOT NULL,
            status   VARCHAR(20) NOT NULL DEFAULT 'pending'
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS packages (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        VARCHAR(200) NOT NULL,
            slug        VARCHAR(220) NOT NULL,
            description TEXT,
            picture_url VARCHAR(500),
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            is_active   BOOLEAN  DEFAULT TRUE,
            is_featured BOOLEAN  DEFAULT FALSE,
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS package_coupons (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            package_id UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
            coupon_id  UUID NOT NULL REFERENCES coupons(id)  ON DELETE CASCADE,
            UNIQUE (package_id, coupon_id)
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS payment_tokens (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token              VARCHAR(512) UNIQUE NOT NULL,
            order_id           UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            payment_intent_id  VARCHAR(255) NOT NULL,
            expires_at         TIMESTAMP NOT NULL,
            used_at            TIMESTAMP,
            is_used            BOOLEAN  DEFAULT FALSE,
            site_origin        VARCHAR(255),
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    run("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name       VARCHAR(100) NOT NULL,
            email      VARCHAR(150) NOT NULL,
            subject    VARCHAR(255) NOT NULL,
            message    TEXT         NOT NULL,
            status     VARCHAR(20)  NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'resolved')),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # ══════════════════════════════════════════════════════════════
    # ALTER TABLE – add columns that were introduced via .sql files
    # (all idempotent: ADD COLUMN IF NOT EXISTS)
    # ══════════════════════════════════════════════════════════════

    # ── coupons ───────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS price               FLOAT          DEFAULT 0.0",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS redeem_code         VARCHAR(100)",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS brand               VARCHAR(100)",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS category_id         UUID           REFERENCES categories(id) ON DELETE SET NULL",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS availability_type   VARCHAR(20)    DEFAULT 'online'",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS picture_url         VARCHAR(500)",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS is_package_coupon   BOOLEAN        DEFAULT FALSE",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS stock               INTEGER",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS is_featured         BOOLEAN        DEFAULT FALSE",
        "ALTER TABLE coupons ADD COLUMN IF NOT EXISTS pricing             JSONB",
    ]:
        run(stmt)

    # ── users ─────────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email                VARCHAR(255) UNIQUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp                  VARCHAR(10)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expiry           TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth        DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender               VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS country_of_residence VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS home_address         VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS town                 VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS state_province       VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS postal_code          VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS address_country      VARCHAR(100)",
    ]:
        run(stmt)

    # ── payments ──────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255) UNIQUE",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_client_secret      VARCHAR(255)",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS currency                  VARCHAR(3)   DEFAULT 'USD'",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS gateway                   VARCHAR(50)  DEFAULT 'stripe'",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_metadata          JSONB",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS completed_at              TIMESTAMP",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at                TIMESTAMP    DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS updated_at                TIMESTAMP    DEFAULT CURRENT_TIMESTAMP",
    ]:
        run(stmt)

    # payments: unique order constraint (idempotent via DO $$)
    run("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'unique_order_payment'
            ) THEN
                ALTER TABLE payments ADD CONSTRAINT unique_order_payment UNIQUE (order_id);
            END IF;
        END $$
    """)

    # ── orders ────────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_state              VARCHAR(20)  DEFAULT 'awaiting_payment'",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS stripe_payment_intent_id   VARCHAR(255)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS currency                   VARCHAR(3)   DEFAULT 'USD' NOT NULL",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS webhook_url                VARCHAR(500)",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS reference_id               VARCHAR(255)",
    ]:
        run(stmt)

    # ── cart_items ────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS package_id UUID REFERENCES packages(id)",
        "ALTER TABLE cart_items ALTER COLUMN coupon_id DROP NOT NULL",
    ]:
        run(stmt)

    # ── order_items ───────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE order_items ALTER COLUMN coupon_id DROP NOT NULL",
        "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS package_id UUID REFERENCES packages(id)",
    ]:
        run(stmt)

    # ── user_coupons ──────────────────────────────────────────────
    run("ALTER TABLE user_coupons ADD COLUMN IF NOT EXISTS used_at TIMESTAMP NULL")

    # ── packages ──────────────────────────────────────────────────
    for stmt in [
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS avg_rating      FLOAT   DEFAULT 0.0",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS total_sold      INTEGER DEFAULT 0",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS country         VARCHAR(100)",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS brand           VARCHAR(100)",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS discount        FLOAT",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP",
        "ALTER TABLE packages ADD COLUMN IF NOT EXISTS brand_url       VARCHAR(500)",
    ]:
        run(stmt)

    # packages.slug: drop unique constraint (migration 015)
    run("ALTER TABLE packages DROP CONSTRAINT IF EXISTS packages_slug_key")

    # ══════════════════════════════════════════════════════════════
    # INDEXES  (all idempotent: CREATE INDEX IF NOT EXISTS)
    # ══════════════════════════════════════════════════════════════

    indexes = [
        # categories
        "CREATE INDEX IF NOT EXISTS idx_categories_name      ON categories(name)",
        "CREATE INDEX IF NOT EXISTS idx_categories_slug      ON categories(slug)",
        "CREATE INDEX IF NOT EXISTS idx_categories_is_active ON categories(is_active)",
        # regions
        "CREATE INDEX IF NOT EXISTS idx_regions_name      ON regions(name)",
        "CREATE INDEX IF NOT EXISTS idx_regions_slug      ON regions(slug)",
        "CREATE INDEX IF NOT EXISTS idx_regions_is_active ON regions(is_active)",
        # countries
        "CREATE INDEX IF NOT EXISTS idx_countries_name         ON countries(name)",
        "CREATE INDEX IF NOT EXISTS idx_countries_slug         ON countries(slug)",
        "CREATE INDEX IF NOT EXISTS idx_countries_country_code ON countries(country_code)",
        "CREATE INDEX IF NOT EXISTS idx_countries_region_id    ON countries(region_id)",
        "CREATE INDEX IF NOT EXISTS idx_countries_is_active    ON countries(is_active)",
        # coupon_countries
        "CREATE INDEX IF NOT EXISTS idx_coupon_countries_coupon_id  ON coupon_countries(coupon_id)",
        "CREATE INDEX IF NOT EXISTS idx_coupon_countries_country_id ON coupon_countries(country_id)",
        # coupons
        "CREATE INDEX IF NOT EXISTS idx_coupons_category_id        ON coupons(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_coupons_availability_type  ON coupons(availability_type)",
        "CREATE INDEX IF NOT EXISTS idx_coupons_is_featured        ON coupons(is_featured) WHERE is_featured = TRUE",
        "CREATE INDEX IF NOT EXISTS idx_coupons_code               ON coupons(code)",
        "CREATE INDEX IF NOT EXISTS idx_coupons_is_active          ON coupons(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_coupons_active_list        ON coupons(is_active, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_coupons_title_lower        ON coupons(LOWER(title))",
        "CREATE INDEX IF NOT EXISTS idx_coupons_brand_lower        ON coupons(LOWER(brand))",
        # users
        "CREATE INDEX IF NOT EXISTS idx_users_id             ON users(id)",
        "CREATE INDEX IF NOT EXISTS idx_users_phone          ON users(country_code, phone_number)",
        "CREATE INDEX IF NOT EXISTS idx_users_email          ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at     ON users(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active      ON users(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_users_full_name_lower ON users(LOWER(full_name))",
        # payments
        "CREATE INDEX IF NOT EXISTS idx_payments_stripe_pi ON payments(stripe_payment_intent_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_order_id  ON payments(order_id)",
        # payment_tokens
        "CREATE INDEX IF NOT EXISTS idx_payment_tokens_token   ON payment_tokens(token)",
        "CREATE INDEX IF NOT EXISTS idx_payment_tokens_expires ON payment_tokens(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_payment_tokens_order   ON payment_tokens(order_id)",
        # orders
        "CREATE INDEX IF NOT EXISTS idx_orders_stripe_pi      ON orders(stripe_payment_intent_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_status    ON orders(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_id        ON orders(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_created   ON orders(user_id, created_at DESC)",
        # order_items
        "CREATE INDEX IF NOT EXISTS idx_order_items_order_id   ON order_items(order_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_reference_id ON orders(reference_id)",
        "CREATE INDEX IF NOT EXISTS ix_order_items_package_id  ON order_items(package_id)",
        # cart_items
        "CREATE INDEX IF NOT EXISTS idx_cart_items_user_id     ON cart_items(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_cart_items_user_coupon ON cart_items(user_id, coupon_id)",
        # user_coupons
        "CREATE INDEX IF NOT EXISTS idx_user_coupons_user_id   ON user_coupons(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_coupons_composite ON user_coupons(user_id, coupon_id)",
        "CREATE INDEX  IF NOT EXISTS idx_user_coupons_used_at  ON user_coupons(used_at)",
        # packages
        "CREATE INDEX IF NOT EXISTS ix_packages_category              ON packages(category_id)",
        "CREATE INDEX IF NOT EXISTS ix_packages_active                ON packages(is_active)",
        "CREATE INDEX IF NOT EXISTS ix_packages_featured              ON packages(is_featured) WHERE is_featured = TRUE",
        "CREATE INDEX IF NOT EXISTS ix_packages_slug_non_unique       ON packages(slug)",
        # package_coupons
        "CREATE INDEX IF NOT EXISTS ix_package_coupons_package ON package_coupons(package_id)",
        "CREATE INDEX IF NOT EXISTS ix_package_coupons_coupon  ON package_coupons(coupon_id)",
        # contact_messages
        "CREATE INDEX IF NOT EXISTS idx_contact_messages_status     ON contact_messages(status)",
        "CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON contact_messages(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_contact_messages_email      ON contact_messages(email)",
    ]
    for idx in indexes:
        run(idx)

    # ══════════════════════════════════════════════════════════════
    # TRIGGERS
    # ══════════════════════════════════════════════════════════════

    run("""
        CREATE OR REPLACE FUNCTION update_contact_messages_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Create trigger only if it does not already exist
    run("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'trigger_update_contact_messages_updated_at'
            ) THEN
                CREATE TRIGGER trigger_update_contact_messages_updated_at
                    BEFORE UPDATE ON contact_messages
                    FOR EACH ROW
                    EXECUTE FUNCTION update_contact_messages_updated_at();
            END IF;
        END $$
    """)

    # ══════════════════════════════════════════════════════════════
    # SEED DATA  (idempotent ON CONFLICT DO NOTHING)
    # ══════════════════════════════════════════════════════════════

    run("""
        INSERT INTO categories (name, slug, description, icon, display_order, is_active) VALUES
        ('Pets & Pet Supplies',       'pets-pet-supplies',      'Pet food, toys, grooming products, accessories, and pet health items',                 '🐾', 1, TRUE),
        ('Automotive & Car Care',     'automotive-car-care',    'Car cleaning, detailing, spare parts, repairs, tires, and accessories',               '🚗', 2, TRUE),
        ('Home Furnishings & Decor',  'home-furnishings-decor', 'Furniture, sofas, beds, pillows, bedding, rugs, and lighting',                        '🏠', 3, TRUE),
        ('Electronics & Gadgets',     'electronics-gadgets',    'Smartphones, laptops, accessories, audio devices, and smart home products',            '📱', 4, TRUE),
        ('Fashion & Apparel',         'fashion-apparel',        'Clothing, shoes, bags, and accessories for men, women, and children',                  '👗', 5, TRUE),
        ('Beauty & Personal Care',    'beauty-personal-care',   'Skincare, cosmetics, hair care, grooming, and hygiene products',                       '💄', 6, TRUE),
        ('Food & Grocery',            'food-grocery',           'Online grocery shopping, meal kits, snacks, and specialty foods',                      '🛒', 7, TRUE),
        ('Health & Wellness',         'health-wellness',        'Vitamins, supplements, fitness products, and wellness services',                       '🏃', 8, TRUE),
        ('Tools & DIY',               'tools-diy',              'Hand tools, power tools, workshop equipment, and DIY supplies',                        '🔧', 9, TRUE),
        ('Travel & Experiences',      'travel-experiences',     'Hotels, flights, car rentals, tours, and experience bookings',                         '✈️', 10, TRUE)
        ON CONFLICT (slug) DO NOTHING
    """)

    run("""
        INSERT INTO regions (name, slug, description, display_order, is_active) VALUES
        ('Asia',          'asia',          'Countries in the Asian continent',    1, TRUE),
        ('Middle East',   'middle-east',   'Countries in the Middle East region', 2, TRUE),
        ('Europe',        'europe',        'Countries in the European continent', 3, TRUE),
        ('North America', 'north-america', 'Countries in North America',          4, TRUE),
        ('South America', 'south-america', 'Countries in South America',          5, TRUE),
        ('Africa',        'africa',        'Countries in the African continent',  6, TRUE)
        ON CONFLICT (slug) DO NOTHING
    """)

    country_inserts = [
        ("India",                "india",                "IN", "asia"),
        ("Thailand",             "thailand",             "TH", "asia"),
        ("Philippines",          "philippines",          "PH", "asia"),
        ("Indonesia",            "indonesia",            "ID", "asia"),
        ("Malaysia",             "malaysia",             "MY", "asia"),
        ("United Arab Emirates", "united-arab-emirates", "AE", "middle-east"),
        ("Saudi Arabia",         "saudi-arabia",         "SA", "middle-east"),
        ("Oman",                 "oman",                 "OM", "middle-east"),
        ("Germany",              "germany",              "DE", "europe"),
        ("United Kingdom",       "united-kingdom",       "GB", "europe"),
        ("France",               "france",               "FR", "europe"),
    ]
    for name, slug, code, region_slug in country_inserts:
        run(f"""
            INSERT INTO countries (name, slug, country_code, region_id, is_active)
            SELECT '{name}', '{slug}', '{code}', r.id, TRUE
            FROM regions r WHERE r.slug = '{region_slug}'
            ON CONFLICT (country_code) DO NOTHING
        """)


def downgrade() -> None:
    # Intentionally not implemented – rolling back a baseline migration
    # on production would destroy all data. Use database backups instead.
    raise NotImplementedError(
        "Downgrade of the baseline migration is not supported. "
        "Restore from a database backup if you need to revert."
    )
