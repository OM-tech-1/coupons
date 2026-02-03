from fastapi import FastAPI
from app.api import auth, coupons, users
from app.database import Base, engine
from sqlalchemy import text

# Create tables
Base.metadata.create_all(bind=engine)

# Add new columns if they don't exist (for existing tables)
def run_migrations():
    columns_to_add = [
        ('date_of_birth', 'DATE'),
        ('gender', 'VARCHAR(20)'),
        ('country_of_residence', 'VARCHAR(100)'),
        ('home_address', 'VARCHAR(255)'),
        ('town', 'VARCHAR(100)'),
        ('state_province', 'VARCHAR(100)'),
        ('postal_code', 'VARCHAR(20)'),
        ('address_country', 'VARCHAR(100)')
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
            except Exception:
                pass  # Column already exists or other issue
        conn.commit()

run_migrations()

app = FastAPI(title="Coupon E-commerce API")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
app.include_router(users.router, prefix="/user", tags=["User"])


@app.get("/")
def health_check():
    return {"status": "OK"}