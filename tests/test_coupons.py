"""Tests for coupon endpoints."""


def test_create_coupon_admin(client, admin_user):
    """POST /coupons/ - admin can create coupons."""
    resp = client.post("/coupons/", json={
        "code": "SAVE20",
        "title": "Save 20 Percent",
        "discount_type": "percentage",
        "discount_amount": 20.0,
        "price": 1.99,
        "is_active": True
    }, headers=admin_user["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SAVE20"
    assert data["title"] == "Save 20 Percent"
    assert data["discount_amount"] == 20.0
    assert data["is_active"] is True


def test_create_coupon_regular_user_forbidden(client, regular_user):
    """POST /coupons/ - regular users cannot create coupons."""
    resp = client.post("/coupons/", json={
        "code": "HACK50",
        "title": "Hacker Coupon",
        "discount_type": "percentage",
        "discount_amount": 50.0
    }, headers=regular_user["headers"])
    assert resp.status_code == 403


def test_create_coupon_unauthenticated(client):
    """POST /coupons/ - unauthenticated requests are rejected."""
    resp = client.post("/coupons/", json={
        "code": "ANON50",
        "title": "Anonymous Coupon",
        "discount_type": "percentage",
        "discount_amount": 50.0
    })
    assert resp.status_code == 401


def test_list_coupons(client, sample_coupon):
    """GET /coupons/ - lists all coupons."""
    resp = client.get("/coupons/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(c["code"] == "TEST50" for c in data)


def test_get_coupon_by_id(client, sample_coupon):
    """GET /coupons/{id} - returns a specific coupon."""
    coupon_id = sample_coupon["id"]
    resp = client.get(f"/coupons/{coupon_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == coupon_id
    assert data["code"] == "TEST50"


def test_get_coupon_not_found(client):
    """GET /coupons/{id} - returns 404 for non-existent coupon."""
    resp = client.get("/coupons/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_update_coupon(client, admin_user, sample_coupon):
    """PUT /coupons/{id} - admin can update coupons."""
    coupon_id = sample_coupon["id"]
    resp = client.put(f"/coupons/{coupon_id}", json={
        "title": "Updated Title",
        "discount_amount": 75.0
    }, headers=admin_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["discount_amount"] == 75.0


def test_update_coupon_regular_user_forbidden(client, regular_user, sample_coupon):
    """PUT /coupons/{id} - regular users cannot update coupons."""
    coupon_id = sample_coupon["id"]
    resp = client.put(f"/coupons/{coupon_id}", json={
        "title": "Hacked Title"
    }, headers=regular_user["headers"])
    assert resp.status_code == 403


def test_delete_coupon(client, admin_user, sample_coupon):
    """DELETE /coupons/{id} - admin can delete coupons."""
    coupon_id = sample_coupon["id"]
    resp = client.delete(f"/coupons/{coupon_id}", headers=admin_user["headers"])
    assert resp.status_code == 204


def test_delete_coupon_regular_user_forbidden(client, regular_user, sample_coupon):
    """DELETE /coupons/{id} - regular users cannot delete coupons."""
    coupon_id = sample_coupon["id"]
    resp = client.delete(f"/coupons/{coupon_id}", headers=regular_user["headers"])
    assert resp.status_code == 403


def test_duplicate_coupon_code(client, admin_user, sample_coupon):
    """POST /coupons/ - rejects duplicate coupon codes."""
    resp = client.post("/coupons/", json={
        "code": "TEST50",
        "title": "Duplicate Code",
        "discount_type": "percentage",
        "discount_amount": 10.0
    }, headers=admin_user["headers"])
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_search_coupons(client, sample_coupon):
    """GET /coupons/?search= - search by title."""
    resp = client.get("/coupons/?search=Test")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


def test_track_coupon_view(client, sample_coupon):
    """POST /coupons/{id}/view - tracks a coupon view."""
    coupon_id = sample_coupon["id"]
    resp = client.post(f"/coupons/{coupon_id}/view?session_id=test-session-123")
    assert resp.status_code == 201
    data = resp.json()
    assert data["message"] == "View tracked"


def test_claim_coupon(client, regular_user, sample_coupon):
    """POST /coupons/{id}/claim - user can claim a coupon."""
    coupon_id = sample_coupon["id"]
    resp = client.post(f"/coupons/{coupon_id}/claim", headers=regular_user["headers"])
    assert resp.status_code == 201
    assert "coupon_id" in resp.json()
