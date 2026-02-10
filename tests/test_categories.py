"""Tests for category endpoints."""


def test_create_category_admin(client, admin_user):
    """POST /categories/ - admin can create categories."""
    resp = client.post("/categories/", json={
        "name": "Food & Drink",
        "slug": "food-drink",
        "description": "Food and beverage coupons"
    }, headers=admin_user["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Food & Drink"
    assert data["slug"] == "food-drink"
    assert data["is_active"] is True


def test_create_category_regular_user_forbidden(client, regular_user):
    """POST /categories/ - regular users cannot create categories."""
    resp = client.post("/categories/", json={
        "name": "Hacked Category",
        "slug": "hacked"
    }, headers=regular_user["headers"])
    assert resp.status_code == 403


def test_list_categories(client, sample_category):
    """GET /categories/ - lists all categories."""
    resp = client.get("/categories/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(c["slug"] == "electronics" for c in data)


def test_get_category_by_slug(client, sample_category):
    """GET /categories/{slug} - returns a specific category."""
    resp = client.get("/categories/electronics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Electronics"


def test_get_category_not_found(client):
    """GET /categories/{slug} - returns 404 for non-existent slug."""
    resp = client.get("/categories/nonexistent-slug")
    assert resp.status_code == 404


def test_update_category(client, admin_user, sample_category):
    """PUT /categories/{id} - admin can update categories."""
    cat_id = sample_category["id"]
    resp = client.put(f"/categories/{cat_id}", json={
        "name": "Updated Electronics",
        "description": "Updated description"
    }, headers=admin_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Electronics"


def test_duplicate_category_slug(client, admin_user, sample_category):
    """POST /categories/ - rejects duplicate slugs."""
    resp = client.post("/categories/", json={
        "name": "Another Electronics",
        "slug": "electronics"
    }, headers=admin_user["headers"])
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_delete_category(client, admin_user, sample_category):
    """DELETE /categories/{id} - admin can delete categories."""
    cat_id = sample_category["id"]
    resp = client.delete(f"/categories/{cat_id}", headers=admin_user["headers"])
    assert resp.status_code == 204


def test_categories_with_counts(client, sample_category):
    """GET /categories/with-counts - returns categories with coupon counts."""
    resp = client.get("/categories/with-counts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert "coupon_count" in data[0]
