"""
Test configuration and shared fixtures.
Uses SQLite in-memory database for CI (no external services needed).

The key challenge is that the app uses PostgreSQL UUID columns which don't
work with SQLite. We handle this by:
1. Patching the dialect UUID BEFORE any model imports
2. Disabling rate limiting
3. Using an in-memory SQLite database
"""
import os
import uuid as _uuid

# ---- Set test environment FIRST ----
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-key-for-ci"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["REDIS_URL"] = ""
os.environ["PAYMENT_TOKEN_SECRET"] = "test-payment-token-secret"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake_key_for_ci"
os.environ["ENVIRONMENT"] = "test"

# ---- Patch UUID for SQLite BEFORE any model imports ----
from sqlalchemy import String, TypeDecorator
import sqlalchemy.dialects.postgresql as pg_dialect


class SQLiteCompatUUID(TypeDecorator):
    """Stores UUIDs as strings for SQLite compatibility."""
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=True, **kwargs):
        self.as_uuid = as_uuid
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and self.as_uuid:
            if isinstance(value, _uuid.UUID):
                return value
            return _uuid.UUID(value)
        return value


# Replace the PostgreSQL UUID type before any models use it
pg_dialect.UUID = SQLiteCompatUUID

# ---- NOW import app modules ----
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.middleware.rate_limit import limiter

# Disable rate limiting in tests
limiter.enabled = False

# SQLite in-memory engine
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a clean database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with DB override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Valid US phone numbers
ADMIN_PHONE = {"country_code": "+1", "number": "2025551234"}
REGULAR_PHONE = {"country_code": "+1", "number": "2025559876"}


@pytest.fixture
def admin_user(client, db):
    """Register an admin user and return login token."""
    client.post("/auth/register", json={
        **ADMIN_PHONE, "password": "adminpass123", "full_name": "Test Admin"
    })
    from app.models.user import User
    user = db.query(User).filter(User.phone_number == "+12025551234").first()
    if user:
        user.role = "ADMIN"
        db.commit()
    resp = client.post("/auth/login", json={
        **ADMIN_PHONE, "password": "adminpass123"
    })
    data = resp.json()
    token = data["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def regular_user(client):
    """Register a regular user and return login token."""
    client.post("/auth/register", json={
        **REGULAR_PHONE, "password": "userpass123", "full_name": "Test User"
    })
    resp = client.post("/auth/login", json={
        **REGULAR_PHONE, "password": "userpass123"
    })
    data = resp.json()
    token = data["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def sample_category(client, admin_user):
    """Create a sample category."""
    resp = client.post("/categories/", json={
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic devices and gadgets"
    }, headers=admin_user["headers"])
    return resp.json()


@pytest.fixture
def sample_coupon(client, admin_user):
    """Create a sample coupon."""
    resp = client.post("/coupons/", json={
        "code": "TEST50",
        "title": "Test 50% Off",
        "description": "Test coupon",
        "discount_type": "percentage",
        "discount_amount": 50.0,
        "price": 2.99,
        "is_active": True
    }, headers=admin_user["headers"])
    return resp.json()
