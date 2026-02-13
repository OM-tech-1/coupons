from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api import auth, coupons, users, cart, orders, categories, regions, countries, admin
from app.api.stripe import payments_router, webhooks_router
from app.api.external.payment import router as external_payment_router
from app.database import Base, engine, SessionLocal
from app.middleware.rate_limit import setup_rate_limiting
from sqlalchemy import text
import os

# Import all models to ensure they're registered BEFORE Base.metadata.create_all()
# This is critical for SQLAlchemy to properly resolve relationships
from app.models import (
    User, Coupon, UserCoupon, CartItem, Order, Payment, PaymentToken,
    Category, Region, Country, CouponCountry
)

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
    
    # Coupon columns
    coupon_columns = [
        ('price', 'FLOAT DEFAULT 0.0'),
        ('redeem_code', 'VARCHAR(100)'),
        ('brand', 'VARCHAR(100)'),
        ('category_id', 'UUID'),
        ('availability_type', "VARCHAR(20) DEFAULT 'online'")
    ]

    # Order columns
    order_columns = [
        ('webhook_url', 'VARCHAR(500)')
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

        for col_name, col_type in order_columns:
            try:
                conn.execute(text(f'ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
            except Exception:
                pass
        
        conn.commit()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SHOW_DOCS = ENVIRONMENT != "production"

app = FastAPI(
    title="Coupon E-commerce API",
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None
)

# CORS configuration for payment domain
PAYMENT_UI_DOMAIN = os.getenv("PAYMENT_UI_DOMAIN", "https://payment.vouchergalaxy.com")
MAIN_SITE_DOMAIN = os.getenv("MAIN_SITE_DOMAIN", "https://vouchergalaxy.com")

allowed_origins = [
    PAYMENT_UI_DOMAIN,
    MAIN_SITE_DOMAIN,
    "https://www.vouchergalaxy.com",  # Main site (www)
    "https://api.vouchergalaxy.com",  # API domain
    "https://cms.vouchergalaxy.com",  # CMS domain
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # Local API
]

# Setup rate limiting
setup_rate_limiting(app)

# Add GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cache-Control headers for public read-only endpoints
PUBLIC_CACHEABLE_PREFIXES = ("/coupons", "/categories", "/countries", "/regions")

@app.middleware("http")
async def cache_control_middleware(request, call_next):
    response = await call_next(request)
    path = request.url.path

    if (
        request.method == "GET"
        and any(path.startswith(p) for p in PUBLIC_CACHEABLE_PREFIXES)
        and "authorization" not in request.headers
    ):
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store"

    return response

# CORS must be the last middleware added so it's the outermost wrapper
# This ensures CORS headers are added even to 429/500 responses from other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(coupons.router, prefix="/coupons", tags=["Coupons"])
app.include_router(users.router, prefix="/user", tags=["User"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(regions.router, prefix="/regions", tags=["Regions"])
app.include_router(countries.router, prefix="/countries", tags=["Countries"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Stripe payment routes
app.include_router(payments_router)
app.include_router(webhooks_router)

# External Integration Routes
app.include_router(external_payment_router, prefix="/api/v1/external", tags=["External Integrations"])


@app.get("/")
def health_check():
    """Basic health check endpoint."""
    return {"status": "OK", "version": "2.0.1"} # Production Release: Stripe Live Keys Configured


@app.get("/health")
def detailed_health_check():
    """Detailed health check with database connection status."""
    status = {"status": "OK", "database": "unknown"}
    
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        status["database"] = "connected"
    except Exception as e:
        status["status"] = "degraded"
        status["database"] = f"error: {str(e)}"
    
    return status