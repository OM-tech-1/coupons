# VoucherGalaxy Platform

A comprehensive **FastAPI-based** coupon and voucher marketplace featuring **Curated Packages (Bundles)**, **Multi-Currency Pricing**, **Category & Geography-based discovery**, built for high performance and scalability.

## Key Features

### Packages & Bundles (New in v2)
- Group multiple individual coupons into themed Packages (e.g., \"Summer Travel Bundle\").
- Auto-calculated dynamic pricing based on the underlying coupons.
- Purchase entire bundles with a single API call.

### Multi-Currency & Pricing Options
- Built-in multi-currency support (e.g., AED, SAR, OMR, INR, USD).
- Coupons and Packages can have specific pricing tailored to each currency.

### Smart Discovery
- **10 Curated Categories**: Pets, Automotive, Home, Electronics, Fashion, Beauty, Food, Health, DIY, Travel.
- **Geographic Organization**: Browse deals by 6 regions and 11+ countries.
- **Real-Time Analytics**: Trending, Featured, and Recently Viewed items using Redis.

### Full E-commerce & Wallet
- **Unified Authentication**: Single login/registration flow using Email & Phone.
- **Digital Wallet**: Users can track purchased coupons and view revealed redeem codes.
- **Shopping Cart**: Add individual coupons or full packages to the cart.
- **Hybrid Payments**: Secure checkout with Stripe Payment Intents or Hosted Payment Links (with HMAC signatures).
- **PDF Invoices**: Auto-generated receipts for every order.

### Performance Optimized
- Redis caching for real-time stock and view counters.
- Database connection pooling & robust SQLAlchemy 2.0 ORM.
- Rate limiting to prevent abuse.

---

## Project Structure

```
coupons/
 app/
  api/       # API route handlers (Coupons, Packages, Cart, Auth, etc.)
  models/      # SQLAlchemy ORM models
  schemas/     # Pydantic validation schemas
  services/     # Business logic & Stripe integrations
  middleware/    # Rate limiting & security
  config.py     # Environment configuration
  database.py    # PostgreSQL database connection
  main.py      # FastAPI application root
 docs/         # Official Documentation
  API_DOCUMENTATION.md     # Complete API Reference (v2.0.1)
  POSTMAN_COLLECTION_GUIDE.md  # Postman setup instructions
  FRONTEND_GUIDE.md       # Frontend integration examples
  ...
 scripts/       # Utility scripts for DB management
 tests/        # Pytest test suite
 migrations/      # SQL migration files
 VoucherGalaxy_Complete_API.postman_collection.json # Postman export
 .env         # Environment variables
```

---

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 12+ 
- **Caching**: Redis
- **Authentication**: JWT (JSON Web Tokens)
- **ORM**: SQLAlchemy 2.0+ & Pydantic v2
- **PDF Generation**: ReportLab
- **Payments**: Stripe SDK

---

## Local Setup & Installation

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file based on your environment:
```env
# Database & Redis
DATABASE_URL=postgresql://user:password@localhost/coupons_db
REDIS_URL=redis://localhost:6379/0

# JWT Auth
JWT_SECRET=your-super-secret-key-at-least-32-chars-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Payment Link HMAC
PAYMENT_LINK_SECRET=your_hmac_secret_key
```

### 3. Database Initialization
The app creates tables automatically. To seed initial data (Categories, Countries, etc):
```bash
psql $DATABASE_URL -f migrations/002_add_categories_and_geography.sql
psql $DATABASE_URL -f migrations/add_indexes.sql
psql $DATABASE_URL -f migrations/016_create_contact_messages.sql
```

### 4. Create Admin User
```bash
python3 create_admin.py
# Creates: admin@example.com / afsal@123 / +917907975711
```

### 5. Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Swagger UI will be available at `http://localhost:8000/docs`. *(Note: Swagger is intentionally disabled in production for security).*

---

## Documentation Reference

For all API endpoints, request payloads, response schemas, error codes, and architectural decisions, please refer to the main documentation file:

 **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)**

For testing the API, import the included Postman Collection:
 **[VoucherGalaxy_Complete_API.postman_collection.json](VoucherGalaxy_Complete_API.postman_collection.json)**

---

## Deployment

The platform is containerized and includes a `Dockerfile` and `gunicorn.conf.py` for production WSGI deployment. It is currently configured for CI/CD via GitHub Actions.

```bash
docker build -t vouchergalaxy-api .
docker run -p 8000:8000 --env-file .env vouchergalaxy-api
```
