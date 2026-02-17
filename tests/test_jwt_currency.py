import pytest
from fastapi.testclient import TestClient
from jose import jwt
from app.main import app
from app.config import JWT_SECRET, JWT_ALGORITHM
import uuid

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_jwt_contains_currency(client):
    """Test that login response contains correct currency in JWT"""
    # 1. Register INR user (Use valid format: +91 9xxxxxxxxx)
    # Generate unique 9-digit suffix
    suffix = str(uuid.uuid4().int)[:9]
    number = f"9{suffix}"
    
    # Register payload must match UserCreate schema (country_code + number required)
    register_payload = {
        "country_code": "+91",
        "number": number,
        "full_name": "JWT Test User",
        "password": "password123"
    }
    
    # Register
    reg_response = client.post("/auth/register", json=register_payload)
    assert reg_response.status_code == 200, f"Register failed: {reg_response.json()}"
    
    # Login - Schema expects country_code and number separately
    login_payload = {
        "country_code": "+91",
        "number": number,
        "password": "password123"
    }
    response = client.post("/auth/login", json=login_payload)
    
    # DEBUG: Print response if error
    if response.status_code != 200:
        print(f"Login failed {response.status_code}: {response.json()}")
        
    assert response.status_code == 200
    
    # Decode token
    token = response.json()["access_token"]
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    
    # Verify currency is present and correct
    assert "currency" in payload
    assert payload["currency"] == "INR"

def test_jwt_currency_default(client):
    """Test that unknown country code defaults to USD in JWT"""
    # 1. Register generic user (+1 202xxxxxxx)
    suffix = str(uuid.uuid4().int)[:7]
    number = f"202{suffix}"
    
    # Register payload must match UserCreate schema
    register_payload = {
        "country_code": "+1",
        "number": number,
        "full_name": "JWT Test User Generic",
        "password": "password123"
    }
    
    # Register
    reg_response = client.post("/auth/register", json=register_payload)
    assert reg_response.status_code == 200, f"Register failed: {reg_response.json()}"
    
    login_payload = {
        "country_code": "+1",
        "number": number,
        "password": "password123"
    }
    response = client.post("/auth/login", json=login_payload)
    
    # DEBUG: Print response if error
    if response.status_code != 200:
        print(f"Login failed {response.status_code}: {response.json()}")
        
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    
    assert "currency" in payload
    assert payload["currency"] == "USD"
