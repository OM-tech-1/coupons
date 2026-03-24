# VoucherGalaxy Platform - Detailed Architecture Document

## 1. System Overview

VoucherGalaxy is a comprehensive backend platform designed for a high-performance coupon and voucher marketplace. It supports individual coupons, curated packages (bundles), multi-currency pricing, and smart discovery features such as geography-based and category-based filtering.

The platform is engineered using a modern service-oriented architecture, relying on **FastAPI** as the core web framework for asynchronous request handling, **PostgreSQL** as the primary relational database, and **Redis** for caching, rate limiting, and real-time state management. 

---

## 2. High-Level Architecture

The system follows a standard multi-tier (N-Tier) architectural pattern, enforcing separation of concerns:

- **Presentation Layer (API Routers):** Defines RESTful endpoints. Responsible for routing HTTP requests, performing input validation using Pydantic, and structuring JSON responses. Uses FastAPI's dependency injection system for authentication and database sessions.
- **Business Logic Layer (Services):** Contains pure business logic. Prevents fat controllers by orchestrating complex flows (e.g., checkout, token generation, package aggregation) and abstracting third-party integrations (Stripe, AWS S3, Email Providers).
- **Data Access Layer (Models & Schemas):**
  - *Models (SQLAlchemy):* Represents the physical database schema and relationships.
  - *Schemas (Pydantic):* Represents the Data Transfer Objects (DTOs) used for API requests and responses.
- **Background & Asynchronous Processing:** Uses FastAPI's `BackgroundTasks` for non-blocking operations like sending emails and synchronizing Redis counters to PostgreSQL.
- **Caching & Ephemeral State Layer:** Redis is used for high-velocity data (view counters, temporary stock locks) and rate limiting.

---

## 3. Technology Stack

- **Core Framework:** FastAPI 0.104+
- **Language:** Python 3.10+
- **Database:** PostgreSQL 12+ 
- **ORM & DB Migrations:** SQLAlchemy 2.0+ (using `psycopg2-binary`) & Raw SQL scripts (`migrations/`)
- **Caching & Rate Limiting:** Redis
- **Data Validation & Serialization:** Pydantic v2
- **Authentication & Security:** JWT (JSON Web Tokens), PBKDF2 Password Hashing
- **Transactional Emails:** `fastapi-mail` (SMTP integration for OTPs and Reset Links)
- **Payments Processing:** Stripe API SDK (Payment Intents & Webhooks)
- **Object Storage (Media):** AWS S3 (via `boto3`)
- **Document Generation:** ReportLab (for PDF Invoices)
- **Testing:** Pytest Test Suite
- **Deployment & Infra:** Docker, Gunicorn (with Uvicorn workers), GitHub Actions (CI/CD)

---

## 4. Directory Structure

```text
coupons/
├── app/                  # Application Root
│   ├── api/              # API Routers (Controllers handling HTTP req/res)
│   ├── models/           # SQLAlchemy Data Models (Entities)
│   ├── schemas/          # Pydantic Schemas (DTOs for IO validation)
│   ├── services/         # Core Business Logic & External Adapters
│   ├── middleware/       # Custom Middleware (Rate limits, GZip, Cache-Control)
│   ├── utils/            # Helper functions (Security, Parsers, Auth, Email)
│   ├── config.py         # App configuration management (ENV variables)
│   ├── database.py       # DB Connection pooling and Session factory
│   ├── cache.py          # Redis connection pool and caching helpers
│   └── main.py           # Application Entrypoint, CORS config
├── docs/                 # Platform Documentation (API, Postman, Architecture)
├── migrations/           # SQL migration scripts for schema changes
├── scripts/              # Utility scripts (e.g., db seeders)
├── tests/                # Pytest Test Suite
├── .github/workflows/    # CI/CD pipelines (ci-cd.yml)
├── create_admin.py       # CLI script for bootstrapping the first admin user
└── Dockerfile            # Container configuration
```

---

## 5. Core Domain Models (Data Layer)

The database schema utilizes `UUID` as primary keys for security and distribution. Key entities include:

### 5.1 User Management
- **`User`**: Central entity for authentication. Attributes include `email`, `phone_number`, `hashed_password`, `role`. Contains extended profile fields (`home_address`, `date_of_birth`, etc.) and OTP fields (`otp`, `otp_expiry`) for password recovery.
- **`ContactMessage`**: Auditable records of customer support queries.

### 5.2 Catalog & Inventory
- **`Category`, `Region`, `Country`**: Taxonomy entities used for structured discovery.
- **`Coupon`**: Represents a standalone discount voucher. Attributes include `price`, `redeem_code`, `brand`, `picture_url`, and `availability_type`. Linked to a specific `Category`.
- **`Package` (Bundle)**: Aggregates multiple `Coupons` using a many-to-many junction table (`PackageCoupon`). Features dynamic pricing (`discount`), analytical tracking (`total_sold`, `avg_rating`), and geographic targeting (`country`).

### 5.3 E-Commerce & Transactions
- **`CartItem`**: Ephemeral records of items (either `Coupon` or `Package`) a user intends to purchase.
- **`Order` & `OrderItem`**: Represents a finalized purchase intent. Tracks `total_amount`, `currency`, and `status`. Connects to `OrderItems` which snapshot the state and price of the purchased entities.
- **`Payment`**: Tracks Stripe transactions natively. Captures `stripe_charge_id`, `amount`, and `status` to ensure idempotent webhooks and financial reconciliation.

---

## 6. Service & Utility Layer (Business Logic)

The `app/services/` and `app/utils/` directories govern internal operations. Key functionalities include:

### 6.1 Commerce Services
- **`CartService`**: Manages cart operations. Calculates dynamic totals across multi-currency rules.
- **`OrderService`**: Handles the transition from a Cart to a provisional Order. Calculates final subtotals and prepares metadata for Stripe.
- **`InvoiceService`**: Uses ReportLab to generate PDF receipts upon successful payment confirmation.

### 6.2 Content & Catalog Services
- **`PackageService` / `CouponService`**: Handles CRUD operations and complex aggregation logic. Implements filtering and sorting logic optimized to avoid N+1 query problems.
- **`S3Service`**: Connects via `boto3` to AWS S3. Handles secure image uploads (e.g., package thumbnails), enforces strict file extension whitelists (`.png`, `.jpg`), validates chunks up to 5MB, and returns public S3 URLs.

### 6.3 Security, Email & External Services
- **`AuthService` & `Security Utils`**: Manages the generation of JWTs, hashing passwords, verifying OTPs, and maintaining RBAC (Role-Based Access Control) boundaries.
- **`Email Provider` (`utils.email.py`)**: Utilizes `fastapi-mail` to construct and dispatch HTML-formatted transactional emails (e.g., Password Reset Magic Links) via SMTP. Executed asynchronously via `BackgroundTasks`. 
- **`PaymentService` & `ExternalPaymentService`**: Interfaces with the Stripe SDK to generate Payment Intents, construct Hosted Payment Links with HMAC signatures, and process asynchronous HTTP Webhooks for fulfilling orders idempotently.
- **`Redis Cache` (`cache.py`)**: Defines a robust connection pool. Implements list trimming (`redis_lpush_capped`) for "Recently Viewed" coupons and sorted sets (`redis_zincrby`) for trending metrics.

---

## 7. Migration, CLI & Testing Strategy

- **Database Migrations:** Instead of heavy machinery like Alembic, the project maintains explicit idempotency via Raw SQL scripts (`migrations/*.sql`). The `main.py` entrypoint also performs dynamic schema assertions (e.g., `ALTER TABLE ADD COLUMN IF NOT EXISTS`) on application boot to guarantee column availability.
- **CLI Utilities:** Python scripts (like `create_admin.py` and those in `scripts/`) run independently of the ASGI server to bootstrap infrastructure, seed initial categorization data, and create superuser accounts.
- **Pytest:** The `tests/` directory contains unit and integration tests asserting core pathways, mocking external services (Stripe, S3), and verifying API payloads.

---

## 8. Security Architecture

- **Authentication:** Stateless architecture using JSON Web Tokens (JWT). Tokens map `sub` to the internal User `UUID`.
- **Throttling/Rate Limiting:** IP-based request throttling middleware natively protects globally, with tighter restrictions on sensitive endpoints (e.g., OTP generation, Login) to deter brute-forcing.
- **CORS Management:** Strict `allowed_origins` configuration explicitly whitelisting Payment UIs, CMS domains, and canonical production hostnames.
- **Binary Input Sanitization:** Custom `ValidationException` handlers sanitize binary inputs to prevent memory DOS and Unicode Decode crashes on backend encoding.
- **Idempotency:** Payment endpoints utilize reference keys, Stripe Webhook signature validation, and strict DB locking to prevent double-crediting user wallets.

---

## 9. Scalability, Deployment & CI/CD

- **Concurrency:** FastAPI's `async/await` syntax natively handles thousands of concurrent I/O bound connections (HTTP requests, DB queries).
- **Database Pooling:** SQLAlchemy `sessionmaker` uses a connection pool configuration avoiding expensive TCP handshakes per request.
- **Cache-Control Middlewares:** Auto-injects `stale-while-revalidate` caching directive headers for public taxonomies (`/categories`, `/countries`), allowing edge CDNs (like Cloudflare) to absorb reads.
- **Containerization:** The platform is Dockerized (`Dockerfile`) exposing WSGI/ASGI servers. The recommended production pattern runs `gunicorn` with `uvicorn.workers.UvicornWorker` to spawn exactly $N$ worker processes based on CPU core availability.
- **CI/CD Pipelines:** GitHub Actions (`.github/workflows/ci-cd.yml`) automates the test suite execution, container building, and deployment processes upon standard branch merges.
