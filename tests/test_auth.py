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


# ---------------------------------------------------------------------------
# Change Password tests
# ---------------------------------------------------------------------------

STRONG_PASS = "NewSecure@456"


def _register_and_login(client, phone, password="testpass123", full_name="Test User"):
    """Helper: register a user and return a bearer auth header."""
    client.post("/auth/register", json={**phone, "password": password, "full_name": full_name})
    resp = client.post("/auth/login", json={**phone, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_change_password_success(client):
    """POST /auth/change-password returns 200 and the new password works."""
    headers = _register_and_login(client, PHONE_A)
    resp = client.post("/auth/change-password", json={
        "current_password": "testpass123",
        "new_password": STRONG_PASS,
        "confirm_password": STRONG_PASS,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["message"] == "Password updated successfully"

    # Old password should now fail
    resp_old = client.post("/auth/login", json={**PHONE_A, "password": "testpass123"})
    assert resp_old.status_code == 401

    # New password should work
    resp_new = client.post("/auth/login", json={**PHONE_A, "password": STRONG_PASS})
    assert resp_new.status_code == 200


def test_change_password_wrong_current_password(client):
    """POST /auth/change-password returns 403 if current_password is wrong."""
    headers = _register_and_login(client, PHONE_A)
    resp = client.post("/auth/change-password", json={
        "current_password": "WrongPassword!99",
        "new_password": STRONG_PASS,
        "confirm_password": STRONG_PASS,
    }, headers=headers)
    assert resp.status_code == 403
    assert "incorrect" in resp.json()["detail"].lower()


def test_change_password_confirm_mismatch(client):
    """POST /auth/change-password returns 422 if confirm_password != new_password."""
    headers = _register_and_login(client, PHONE_A)
    resp = client.post("/auth/change-password", json={
        "current_password": "testpass123",
        "new_password": STRONG_PASS,
        "confirm_password": "Different@Pass1",
    }, headers=headers)
    assert resp.status_code == 422


def test_change_password_weak_new_password(client):
    """POST /auth/change-password returns 422 if new_password fails strength rules."""
    headers = _register_and_login(client, PHONE_A)
    resp = client.post("/auth/change-password", json={
        "current_password": "testpass123",
        "new_password": "weak",
        "confirm_password": "weak",
    }, headers=headers)
    assert resp.status_code == 422


def test_change_password_missing_token(client):
    """POST /auth/change-password returns 401 when no Bearer token is provided."""
    resp = client.post("/auth/change-password", json={
        "current_password": "testpass123",
        "new_password": STRONG_PASS,
        "confirm_password": STRONG_PASS,
    })
    assert resp.status_code == 401
