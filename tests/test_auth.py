"""Tests for authentication endpoints."""


# Valid US phone numbers for testing
PHONE_A = {"country_code": "+1", "number": "2025551234"}
PHONE_B = {"country_code": "+1", "number": "2025559999"}


def test_register_user(client):
    """POST /auth/register creates a new user."""
    resp = client.post("/auth/register", json={
        **PHONE_A,
        "password": "testpass123",
        "full_name": "John Doe"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "John Doe"
    assert data["role"] == "USER"
    assert data["is_active"] is True


def test_register_duplicate_phone(client):
    """POST /auth/register rejects duplicate phone numbers."""
    payload = {**PHONE_A, "password": "testpass123", "full_name": "John Doe"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_success(client):
    """POST /auth/login returns access token."""
    client.post("/auth/register", json={
        **PHONE_A, "password": "testpass123", "full_name": "John Doe"
    })
    resp = client.post("/auth/login", json={
        **PHONE_A, "password": "testpass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """POST /auth/login rejects wrong password."""
    client.post("/auth/register", json={
        **PHONE_A, "password": "testpass123", "full_name": "John Doe"
    })
    resp = client.post("/auth/login", json={
        **PHONE_A, "password": "wrongpass"
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    """POST /auth/login rejects non-existent user."""
    resp = client.post("/auth/login", json={
        **PHONE_B, "password": "testpass123"
    })
    assert resp.status_code == 401
