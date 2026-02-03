from fastapi import FastAPI
from app.api import auth, coupons, users, cart, orders
from app.database import Base, engine
from sqlalchemy import text

# Create tables
Base.metadata.create_all(bind=engine)

# Add new columns if they don't exist (for existing tables)
def run_migrations():
    # User profile columns
    user_columns = [
        ('email', 'VARCHAR(255)'),
        ('date_of_birth', 'DATE'),
        ('gender', 'VARCHAR(20)'),
        ('country_of_residence', 'VARCHAR(100)'),
        ('home_address', 'VARCHAR(255)'),
        ('town', 'VARCHAR(100)'),
        ('state_province', 'VARCHAR(100)'),
        ('postal_code', 'VARCHAR(20)'),
        ('address_country', 'VARCHAR(100)')
    ]
    
    # Coupon price column
    coupon_columns = [
        ('price', 'FLOAT DEFAULT 0.0')
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in user_columns:
            try:
                conn.execute(text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
            except Exception:
                pass
        
        for col_name, col_type in coupon_columns:
            try:
                conn.execute(text(f'ALTER TABLE coupons ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
            except Exception:
                pass
        
        conn.commit()

run_migrations()

app = FastAPI(title="Coupon E-commerce API")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
app.include_router(users.router, prefix="/user", tags=["User"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])


@app.get("/")
def health_check():
    return {"status": "OK"}