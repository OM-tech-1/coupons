#!/usr/bin/env python3
"""
Migration helper script to apply the categories and geography schema changes
Run this script to apply migration 002_add_categories_and_geography.sql
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Please set it using: export DATABASE_URL='postgresql://user:pass@host/dbname'")
    sys.exit(1)

# Read the migration SQL file
migration_file = "migrations/002_add_categories_and_geography.sql"

try:
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
except FileNotFoundError:
    print(f"ERROR: Migration file not found: {migration_file}")
    sys.exit(1)

# Connect and execute the migration
try:
    print(f"Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print(f"Executing migration: {migration_file}")
    cursor.execute(migration_sql)
    
    # Verify tables were created
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND table_name IN ('categories', 'regions', 'countries', 'coupon_countries')
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print("\n✓ Migration completed successfully!")
    print(f"\nCreated tables: {[t[0] for t in tables]}")
    
    # Count seeded data
    cursor.execute("SELECT COUNT(*) FROM categories")
    cat_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM regions")
    reg_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM countries")
    country_count = cursor.fetchone()[0]
    
    print(f"\nSeeded data:")
    print(f"  - Categories: {cat_count}")
    print(f"  - Regions: {reg_count}")
    print(f"  - Countries: {country_count}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Database migration successful!")
    
except psycopg2.Error as e:
    print(f"\n✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    sys.exit(1)
