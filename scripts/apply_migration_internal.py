import sys
import os

# Ensure app is in path
sys.path.append('/app')

from sqlalchemy import text
from app.database import SessionLocal

def run_migration():
    print("Starting migration...")
    db = SessionLocal()
    try:
        # Check if column exists
        try:
            db.execute(text("SELECT reference_id FROM orders LIMIT 1"))
            print("Column 'reference_id' already exists.")
            return
        except Exception:
            print("Column missing. Adding it...")
            db.rollback()

        # Add column
        try:
            db.execute(text("ALTER TABLE orders ADD COLUMN reference_id VARCHAR(255)"))
            print("Added column 'reference_id'")
        except Exception as e:
            print(f"Error adding column: {e}")

        # Add index
        try:
            db.execute(text("CREATE UNIQUE INDEX ix_orders_reference_id ON orders (reference_id)"))
            print("Added index 'ix_orders_reference_id'")
        except Exception as e:
            print(f"Error adding index: {e}")
            
        db.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
