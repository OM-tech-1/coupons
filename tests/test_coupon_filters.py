"""Tests for coupon filtering."""
import pytest

def test_filter_featured_coupons(client, admin_user):
    """Test filtering by is_featured flag"""
    headers = admin_user["headers"]
    
    # Create a featured coupon
    client.post("/coupons/", json={
        "code": "FEATURED100",
        "title": "Featured Deal",
        "description": "Featured coupon",
        "discount_type": "percentage",
        "discount_amount": 10.0,
        "is_featured": True,
        "is_active": True
    }, headers=headers)
    
    # Create a non-featured coupon
    client.post("/coupons/", json={
        "code": "REGULAR100",
        "title": "Regular Deal",
        "description": "Regular coupon",
        "discount_type": "percentage",
        "discount_amount": 10.0,
        "is_featured": False,
        "is_active": True
    }, headers=headers)
    
    # Filter featured=true
    resp = client.get("/coupons/?is_featured=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for c in data:
        assert c["is_featured"] is True
        
    # Filter featured=false
    resp = client.get("/coupons/?is_featured=false")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for c in data:
        assert c["is_featured"] is False

def test_filter_min_discount(client, admin_user):
    """Test filtering by minimum discount amount"""
    headers = admin_user["headers"]
    
    # Create high discount coupon
    client.post("/coupons/", json={
        "code": "HIGHVAL50",
        "title": "50% Off",
        "description": "Big discount",
        "discount_type": "percentage",
        "discount_amount": 50.0,
        "is_active": True
    }, headers=headers)
    
    # Create low discount coupon
    client.post("/coupons/", json={
        "code": "LOWVAL10",
        "title": "10% Off",
        "description": "Small discount",
        "discount_type": "percentage",
        "discount_amount": 10.0,
        "is_active": True
    }, headers=headers)
    
    # Filter min_discount=40
    resp = client.get("/coupons/?min_discount=40")
    assert resp.status_code == 200
    data = resp.json()
    # Should check that we get at least the high value one, and NO low value ones
    found_high = False
    for c in data:
        assert c["discount_amount"] >= 40.0
        if c["code"] == "HIGHVAL50":
            found_high = True
    assert found_high
