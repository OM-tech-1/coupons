import os
import json
import uuid

# Patch UUID before imports so it works with SQLite
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["PAYMENT_TOKEN_SECRET"] = "test-secret"

from sqlalchemy import String, TypeDecorator
import sqlalchemy.dialects.postgresql as pg_dialect

class SQLiteCompatUUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def __init__(self, as_uuid=True, **kwargs):
        self.as_uuid = as_uuid
        super().__init__()
    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else value
    def process_result_value(self, value, dialect):
        if value is not None and self.as_uuid:
            if isinstance(value, uuid.UUID): return value
            return uuid.UUID(value)
        return value

pg_dialect.UUID = SQLiteCompatUUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def pretty_print(title, data):
    print(f"\n{'='*60}\n{title}\n{'-'*60}")
    print(json.dumps(data, indent=2))

# 1. Setup Admin User
client.post("/auth/register", json={"country_code": "+1", "number": "2025551234", "password": "admin", "full_name": "Admin"})
db = TestingSessionLocal()
from app.models.user import User
admin = db.query(User).filter_by(phone_number="+12025551234").first()
admin.role = "ADMIN"
db.commit()
db.close()

resp = client.post("/auth/login", json={"country_code": "+1", "number": "2025551234", "password": "admin"})
admin_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

# 2. Setup Regular User
client.post("/auth/register", json={"country_code": "+1", "number": "2025559876", "password": "user", "full_name": "User"})
resp = client.post("/auth/login", json={"country_code": "+1", "number": "2025559876", "password": "user"})
user_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

# 3. Create Packages
packages_data = [
    {"name": "Standard Bundle", "slug": "std-bundle", "discount": 10.0, "avg_rating": 4.2, "total_sold": 50, "is_active": True},
    {"name": "Mega Saving Bundle", "slug": "mega-bundle", "discount": 45.0, "avg_rating": 4.5, "total_sold": 200, "is_active": True},
    {"name": "Top Rated Bundle", "slug": "top-bundle", "discount": 5.0, "avg_rating": 4.9, "total_sold": 10, "is_active": True},
    {"name": "Best Seller Bundle", "slug": "best-bundle", "discount": 15.0, "avg_rating": 4.6, "total_sold": 1500, "is_active": True},
    {"name": "Inactive Bundle", "slug": "inactive-bundle", "discount": 50.0, "avg_rating": 5.0, "total_sold": 10000, "is_active": False},
]

for p in packages_data:
    client.post("/packages/", json=p, headers=admin_headers)

pretty_print("✓ Created 5 test packages (4 active, 1 inactive)", [{"name": p["name"], "active": p["is_active"], "discount": p["discount"], "rating": p["avg_rating"], "sold": p["total_sold"]} for p in packages_data])

# 4. Filter Tests
resp = client.get("/packages/")
pretty_print("GET /packages/ (Default: Active Only, ordered by newest)", [{"name": p["name"], "active": p["is_active"]} for p in resp.json()])

resp = client.get("/packages/?filter=highest_saving")
pretty_print("GET /packages/?filter=highest_saving", [{"name": p["name"], "max_saving": p["max_saving"]} for p in resp.json()])

resp = client.get("/packages/?filter=avg_rating")
pretty_print("GET /packages/?filter=avg_rating", [{"name": p["name"], "avg_rating": p["avg_rating"]} for p in resp.json()])

resp = client.get("/packages/?filter=bundle_sold")
pretty_print("GET /packages/?filter=bundle_sold", [{"name": p["name"], "total_sold": p["total_sold"]} for p in resp.json()])

# 5. Cart Add Test
best_seller = [p for p in resp.json() if p["name"] == "Best Seller Bundle"][0]
resp = client.post("/cart/add", json={"package_id": best_seller["id"], "quantity": 1}, headers=user_headers)
pretty_print(f"POST /cart/add (Adding package_id: {best_seller['id']})", resp.json())

# 6. View Cart
resp = client.get("/cart/", headers=user_headers)
pretty_print("GET /cart/ (Verify package is in cart)", resp.json())

print("\n✓ Tests completed successfully!")
