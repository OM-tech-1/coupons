"""Tests for the new wallet endpoints and enriched order responses."""
import pytest


def test_get_order_by_id_has_coupon_details(client, regular_user, sample_coupon):
    """GET /orders/{id} should include coupon details (code, title, description, is_active)"""
    headers = regular_user["headers"]

    # 1. Add to cart + checkout
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    checkout_resp = client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)
    assert checkout_resp.status_code == 200
    order_id = checkout_resp.json()["id"]

    # 2. Get order by ID
    resp = client.get(f"/orders/{order_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # 3. Check items have enriched coupon details
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert "coupon" in item
    coupon = item["coupon"]
    assert coupon["code"] == "TEST50"
    assert coupon["title"] == "Test 50% Off"
    assert coupon["is_active"] is True


def test_my_orders_has_coupon_details(client, regular_user, sample_coupon):
    """GET /orders/ should include coupon details in items"""
    headers = regular_user["headers"]

    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)

    resp = client.get("/orders/", headers=headers)
    assert resp.status_code == 200
    orders = resp.json()

    assert len(orders) >= 1
    item = orders[0]["items"][0]
    assert item["coupon"]["code"] == "TEST50"


def test_wallet_summary(client, regular_user, sample_coupon):
    """GET /user/wallet should return correct summary counts"""
    headers = regular_user["headers"]

    # Before purchase: empty wallet
    resp = client.get("/user/wallet", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_coupons"] == 0

    # Purchase a coupon
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)

    # After purchase
    resp = client.get("/user/wallet", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_coupons"] == 1
    assert data["active"] == 1


def test_wallet_coupons(client, regular_user, sample_coupon):
    """GET /user/wallet/coupons should return coupons with purchased_date"""
    headers = regular_user["headers"]

    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)

    resp = client.get("/user/wallet/coupons", headers=headers)
    assert resp.status_code == 200
    coupons = resp.json()

    assert len(coupons) >= 1
    c = coupons[0]
    assert c["code"] == "TEST50"
    assert c["title"] == "Test 50% Off"
    assert c["status"] == "active"
    assert "purchased_date" in c


def test_individual_coupon_detail(client, regular_user, sample_coupon):
    """GET /user/coupons/{coupon_id} should return detail of owned coupon"""
    headers = regular_user["headers"]

    # Purchase
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)

    coupon_id = sample_coupon["id"]
    resp = client.get(f"/user/coupons/{coupon_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "TEST50"
    assert data["title"] == "Test 50% Off"
    assert data["discount_type"] == "percentage"
    assert data["discount_amount"] == 50.0
    assert data["status"] == "active"


def test_individual_coupon_detail_not_found(client, regular_user):
    """GET /user/coupons/{coupon_id} should return 404 for non-owned coupon"""
    import uuid
    headers = regular_user["headers"]
    random_id = str(uuid.uuid4())
    resp = client.get(f"/user/coupons/{random_id}", headers=headers)
    assert resp.status_code == 404
