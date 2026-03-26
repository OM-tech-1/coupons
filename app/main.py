from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api import auth, coupons, users, cart, orders, categories, regions, countries, admin, packages, contact
from app.api.stripe import payments_router, webhooks_router
from app.api.external.payment import router as external_payment_router
from app.database import SessionLocal
from app.middleware.rate_limit import setup_rate_limiting
from sqlalchemy import text
import os


# Import all models to ensure they're registered BEFORE Base.metadata.create_all()
# This is critical for SQLAlchemy to properly resolve relationships
from app.models import (
    User, Coupon, UserCoupon, CartItem, Order, Payment, PaymentToken,
    Category, Region, Country, Package, PackageCoupon
)
from app.models.contact_message import ContactMessage

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
    try:
        response = await call_next(request)
        path = request.url.path

        # Safely check for authorization header
        has_auth = False
        try:
            has_auth = "authorization" in request.headers
        except Exception:
            pass

        if (
            request.method == "GET"
            and any(path.startswith(p) for p in PUBLIC_CACHEABLE_PREFIXES)
            and not has_auth
        ):
            response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store"

        return response
    except Exception as e:
        # In case of any middleware error, let it propagate but log it
        import logging
        logging.getLogger(__name__).error(f"Cache control middleware error: {e}")
        raise

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
app.include_router(packages.router, prefix="/packages", tags=["Packages"])
app.include_router(contact.router, prefix="/contact", tags=["Contact"])

from app.api import upload
app.include_router(upload.router, prefix="", tags=["Upload"])

# Stripe payment routes
app.include_router(payments_router)
app.include_router(webhooks_router)

# External Integration Routes
app.include_router(external_payment_router, prefix="/api/v1/external", tags=["External Integrations"])


@app.get("/")
def health_check():
    """Basic health check endpoint."""
    return {"status": "OK", "version": "2.0.1"} # Production Release: Stripe Live Keys Configured


# Custom exception handler for validation errors to prevents 500 on binary inputs
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Overrides default validation handling to sanitize binary data in inputs.
    Prevents UnicodeDecodeError when jsonable_encoder tries to encode bytes.
    """
    errors = exc.errors()
    safe_errors = []
    
    for error in errors:
        # Sanitize 'input' field if it is bytes
        if "input" in error and isinstance(error["input"], bytes):
            try:
                # Try validation of utf-8
                error["input"].decode('utf-8')
            except UnicodeDecodeError:
                # Replace with safe placeholder and add a helpful message
                error["input"] = "<binary data>"
                error["msg"] += " (binary data received, expected text)"
        safe_errors.append(error)

    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(safe_errors)},
    )


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