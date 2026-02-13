#!/usr/bin/env python3
"""
Check featured coupons in database
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment before imports
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:YDNWJr8F5Uea%40Er@db.lnswsbkcbkzzyrundjgt.supabase.co:5432/postgres')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Create engine
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Check total coupons
    result = db.execute(text("SELECT COUNT(*) FROM coupons"))
    total = result.scalar()
    print(f'📊 Total coupons: {total}')
    print()
    
    # Check featured coupons
    result = db.execute(text("SELECT COUNT(*) FROM coupons WHERE is_featured = true"))
    featured_count = result.scalar()
    print(f'⭐ Featured coupons: {featured_count}')
    print()
    
    # Check active featured coupons
    result = db.execute(text("SELECT COUNT(*) FROM coupons WHERE is_featured = true AND is_active = true"))
    active_featured_count = result.scalar()
    print(f'✅ Active featured coupons: {active_featured_count}')
    print()
    
    # Show details of featured coupons
    result = db.execute(text("""
        SELECT code, title, is_featured, is_active, created_at 
        FROM coupons 
        WHERE is_featured = true 
        ORDER BY created_at DESC 
        LIMIT 10
    """))
    
    print("📋 Featured coupon details:")
    for row in result:
        status = "✅ Active" if row.is_active else "❌ Inactive"
        print(f"  - {row.code}: {row.title}")
        print(f"    Status: {status}, Featured: {row.is_featured}")
        print()
    
    if featured_count == 0:
        print("⚠️  No featured coupons found in database!")
        print("💡 You need to update coupons to set is_featured=true")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
