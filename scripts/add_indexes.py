"""
Database Migration: Add missing indexes for performance optimization.

Run this script to add indexes to existing tables without data loss.
This is safe to run multiple times (uses IF NOT EXISTS).

Usage:
    .venv/bin/python add_indexes.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

INDEXES = [
    # cart_items
    ("ix_cart_items_user_id", "cart_items", "user_id"),
    ("ix_cart_items_coupon_id", "cart_items", "coupon_id"),

    # user_coupons
    ("ix_user_coupons_user_id", "user_coupons", "user_id"),
    ("ix_user_coupons_coupon_id", "user_coupons", "coupon_id"),

    # orders
    ("ix_orders_user_id", "orders", "user_id"),
    ("ix_orders_status", "orders", "status"),

    # order_items
    ("ix_order_items_order_id", "order_items", "order_id"),
    ("ix_order_items_coupon_id", "order_items", "coupon_id"),

    # payments
    ("ix_payments_status", "payments", "status"),
]

COMPOSITE_INDEXES = [
    ("ix_coupons_active_featured", "coupons", "is_active, is_featured"),
    ("ix_coupons_active_created", "coupons", "is_active, created_at"),
]

UNIQUE_CONSTRAINTS = [
    ("uq_cart_user_coupon", "cart_items", "user_id, coupon_id"),
    ("uq_user_coupon_claim", "user_coupons", "user_id, coupon_id"),
]


def run_migration():
    print("🚀 Adding database indexes...")
    print()

    with engine.connect() as conn:
        # Single-column indexes
        for idx_name, table, column in INDEXES:
            try:
                conn.execute(text(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"
                ))
                print(f"  ✅ {idx_name} on {table}({column})")
            except Exception as e:
                print(f"  ⚠️  {idx_name}: {e}")

        print()

        # Composite indexes
        for idx_name, table, columns in COMPOSITE_INDEXES:
            try:
                conn.execute(text(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})"
                ))
                print(f"  ✅ {idx_name} on {table}({columns})")
            except Exception as e:
                print(f"  ⚠️  {idx_name}: {e}")

        print()

        # Unique constraints (skip if already exists)
        for constraint_name, table, columns in UNIQUE_CONSTRAINTS:
            try:
                # Check if constraint already exists
                result = conn.execute(text(
                    f"SELECT 1 FROM pg_constraint WHERE conname = '{constraint_name}'"
                ))
                if result.fetchone():
                    print(f"  ⏭️  {constraint_name} already exists")
                else:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} UNIQUE ({columns})"
                    ))
                    print(f"  ✅ {constraint_name} on {table}({columns})")
            except Exception as e:
                print(f"  ⚠️  {constraint_name}: {e}")

        conn.commit()

    print()
    print("✅ Migration complete!")


if __name__ == "__main__":
    run_migration()
