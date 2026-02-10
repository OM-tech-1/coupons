import pytest
from app.models.order import Order

def test_download_invoice(client, regular_user, sample_coupon):
    """GET /orders/{id}/invoice - generates PDF invoice"""
    headers = regular_user["headers"]
    
    # 1. Create cart item
    client.post("/cart/add", json={"coupon_id": sample_coupon["id"], "quantity": 1}, headers=headers)
    
    # 2. Checkout (mock)
    checkout_resp = client.post("/orders/checkout", json={"payment_method": "mock"}, headers=headers)
    assert checkout_resp.status_code == 200
    order_id = checkout_resp.json()["id"]
    
    # 3. Download invoice
    resp = client.get(f"/orders/{order_id}/invoice", headers=headers)
    
    # 4. Verify response
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=invoice_" in resp.headers["content-disposition"]
    # Check if we got bytes
    assert len(resp.content) > 0
    # PDF signature
    assert resp.content.startswith(b"%PDF")

def test_download_invoice_not_found(client, regular_user):
    """GET /orders/{id}/invoice - returns 404 for non-existent order"""
    headers = regular_user["headers"]
    import uuid
    random_id = str(uuid.uuid4())
    resp = client.get(f"/orders/{random_id}/invoice", headers=headers)
    assert resp.status_code == 404
