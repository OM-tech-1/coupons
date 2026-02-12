import pytest
from datetime import datetime, timedelta, timezone


def test_mark_coupon_as_used(client, regular_user, sample_coupon):
    """Test marking a coupon as used"""
    auth_headers = regular_user["headers"]
    
    # Purchase the coupon first (add to cart and checkout)
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=auth_headers)
    checkout_resp = client.post("/orders/checkout", json={"payment_method": "mock"}, headers=auth_headers)
    assert checkout_resp.status_code == 200
    
    # Mark coupon as used
    resp = client.post(f"/user/coupons/{sample_coupon['id']}/mark-used", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    # Verify status is "used"
    assert data["status"] == "used"
    assert data["coupon_id"] == sample_coupon["id"]


def test_wallet_summary_with_used_coupons(client, regular_user, sample_coupon, admin_user):
    """Test wallet summary correctly counts used coupons"""
    auth_headers = regular_user["headers"]
    admin_headers = admin_user["headers"]
    
    # Create a second coupon
    resp = client.post("/coupons/", json={
        "code": "SECOND50",
        "title": "Second Coupon",
        "description": "Another test coupon",
        "discount_type": "percentage",
        "discount_amount": 50.0,
        "min_purchase": 0.0,
        "price": 5.0,
        "category_id": sample_coupon["category_id"],
        "is_active": True
    }, headers=admin_headers)
    second_coupon = resp.json()
    
    # Purchase both coupons
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=auth_headers)
    client.post("/cart/add", json={"coupon_id": second_coupon["id"], "quantity": 1}, headers=auth_headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=auth_headers)
    
    # Mark first coupon as used
    client.post(f"/user/coupons/{sample_coupon['id']}/mark-used", headers=auth_headers)
    
    # Check wallet summary
    resp = client.get("/user/wallet", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total_coupons"] == 2
    assert data["used"] == 1
    assert data["active"] == 1
    assert data["expired"] == 0


def test_wallet_coupons_includes_brand(client, regular_user, sample_coupon):
    """Test that wallet coupons response includes brand field"""
    auth_headers = regular_user["headers"]
    
    # Purchase coupon
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=auth_headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=auth_headers)
    
    # Get wallet coupons
    resp = client.get("/user/wallet/coupons", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    assert len(data) > 0
    coupon = data[0]
    assert "brand" in coupon
    assert "status" in coupon


def test_status_priority_used_over_expired(client, regular_user, admin_user):
    """Test that 'used' status takes priority over 'expired'"""
    auth_headers = regular_user["headers"]
    admin_headers = admin_user["headers"]
    
    # Create an expired coupon
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    resp = client.post("/coupons/", json={
        "code": "EXPIRED50",
        "title": "Expired Coupon",
        "description": "An expired test coupon",
        "discount_type": "percentage",
        "discount_amount": 50.0,
        "min_purchase": 0.0,
        "price": 5.0,
        "category_id": None,
        "is_active": True,
        "expiration_date": past_date
    }, headers=admin_headers)
    expired_coupon = resp.json()
    
    # Purchase the expired coupon
    client.post("/cart/add", json={"coupon_id": expired_coupon["id"], "quantity": 1}, headers=auth_headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=auth_headers)
    
    # Mark as used
    resp = client.post(f"/user/coupons/{expired_coupon['id']}/mark-used", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    # Even though it's expired, status should be "used"
    assert data["status"] == "used"


def test_mark_used_unauthorized(client, regular_user, admin_user, sample_coupon):
    """Test that users can only mark their own coupons as used"""
    admin_headers = admin_user["headers"]
    user_headers = regular_user["headers"]
    
    # User purchases coupon
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=user_headers)
    client.post("/orders/checkout", json={"payment_method": "mock"}, headers=user_headers)
    
    # Admin tries to mark user's coupon as used (should fail)
    resp = client.post(f"/user/coupons/{sample_coupon['id']}/mark-used", headers=admin_headers)
    assert resp.status_code == 404  # Not found in admin's collection


def test_mark_nonexistent_coupon_as_used(client, regular_user):
    """Test marking a non-existent coupon as used returns 404"""
    auth_headers = regular_user["headers"]
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    resp = client.post(f"/user/coupons/{fake_id}/mark-used", headers=auth_headers)
    assert resp.status_code == 404
