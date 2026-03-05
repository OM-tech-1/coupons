import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import override_get_db, Base, engine
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
def override_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[override_get_db] = override_db
client = TestClient(app)

try:
    client.post("/packages/", json={
        "name": "Validation Pack", "slug": "validation-pack", "coupon_ids": []
    }, headers={"Authorization": "Bearer admin"})
except Exception as e:
    import traceback
    traceback.print_exc()
