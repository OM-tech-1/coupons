import pytest


def test_coupon_list_includes_category_name(client, admin_user, sample_category):
    """Test that coupon list response includes category name"""
    admin_headers = admin_user["headers"]
    
    # Create a coupon with category
    resp = client.post("/coupons/", json={
        "code": "TESTCAT50",
        "title": "Test Category Coupon",
        "description": "Testing category name in list",
        "discount_type": "percentage",
        "discount_amount": 50.0,
        "min_purchase": 0.0,
        "price": 5.0,
        "category_id": sample_category["id"],
        "is_active": True
    }, headers=admin_headers)
    assert resp.status_code == 201
    
    # Get coupon list
    resp = client.get("/coupons/")
    assert resp.status_code == 200
    data = resp.json()
    
    # Find our test coupon
    # Find our test coupon by title (code is hidden)
    test_coupon = next((c for c in data if c["title"] == "Test Category Coupon"), None)
    assert test_coupon is not None
    
    # Verify category object is present with id and name
    assert "category" in test_coupon
    assert test_coupon["category"] is not None
    assert "id" in test_coupon["category"]
    assert "name" in test_coupon["category"]
    assert test_coupon["category"]["name"] == sample_category["name"]
    assert test_coupon["category"]["id"] == sample_category["id"]
    
    # Verify category_id is still present for backward compatibility
    assert "category_id" in test_coupon
    assert test_coupon["category_id"] == sample_category["id"]
