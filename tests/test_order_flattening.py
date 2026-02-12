import pytest
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon

def test_order_response_flattened_fields(client, regular_user, sample_coupon):
    """Test that order items include flattened coupon fields (title, description, type)"""
    
    # Login
    auth_headers = regular_user["headers"]
    
    # Create an order (add to cart -> checkout)
    # Note: sample_coupon is a dict returned by fixture
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=auth_headers)
    
    # Checkout
    resp = client.post("/orders/checkout", json={"payment_method": "mock"}, headers=auth_headers)
    assert resp.status_code == 200
    order_data = resp.json()
    order_id = order_data["id"]
    
    # Get Order
    resp = client.get(f"/orders/{order_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    
    item = data["items"][0]
    
    # Check flattened fields must match coupon data
    assert "coupon_title" in item
    assert item["coupon_title"] == sample_coupon["title"]
    assert "coupon_description" in item
    assert item["coupon_description"] == sample_coupon["description"]
    assert "coupon_type" in item
    assert item["coupon_type"] == sample_coupon["discount_type"]
    
    # Check nested object still exists and has discount_type
    assert "coupon" in item
    assert item["coupon"]["discount_type"] == sample_coupon["discount_type"]
