import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.jwt import create_access_token
from app.models.coupon import Coupon
import uuid

# Test data
COUPON_DATA = {
    "code": "CURRENCYTEST",
    "title": "Currency Test Coupon",
    "description": "Test multi-currency",
    "discount_type": "percentage",
    "discount_amount": 10.0,
    "price": 100.0,  # Default USD Base Price
    "pricing": {
        "INR": {"price": 8000.0, "discount_amount": 800.0},
        "AED": {"price": 367.0, "discount_amount": 36.7},
        "SAR": {"price": 375.0, "discount_amount": 37.5}
    }
}

@pytest.fixture
def admin_token(db):
    from app.models.user import User
    user = User(
        phone_number="+1999999999",
        role="ADMIN",
        hashed_password="hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    return create_access_token(data={"sub": str(user.id)})

@pytest.fixture
def inr_user_token(db):
    from app.models.user import User
    user = User(
        phone_number="+919876543210",
        role="USER",
        hashed_password="hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    return create_access_token(data={"sub": str(user.id)})

@pytest.fixture
def aed_user_token(db):
    from app.models.user import User
    user = User(
        phone_number="+971501234567",
        role="USER",
        hashed_password="hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    return create_access_token(data={"sub": str(user.id)})

def test_multi_currency_flow(client, admin_token, inr_user_token, aed_user_token, db):
    # 1. Create Coupon with Pricing (Admin)
    response = client.post(
        "/coupons/",
        json=COUPON_DATA,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    created_coupon = response.json()
    coupon_id = created_coupon["id"]
    
    # 2. Anonymous User (Expect USD Default)
    response = client.get(f"/coupons/{coupon_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 100.0
    assert data["discount_amount"] == 10.0
    assert data["currency_symbol"] == "$"
    
    # 3. INR User (Expect INR values)
    response = client.get(
        f"/coupons/{coupon_id}",
        headers={"Authorization": f"Bearer {inr_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 8000.0
    assert data["discount_amount"] == 800.0
    # Note: Symbol might be unicode, check if correct
    assert data["currency_symbol"] == "₹"
    
    # 4. AED User (Expect AED values)
    response = client.get(
        f"/coupons/{coupon_id}",
        headers={"Authorization": f"Bearer {aed_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 367.0
    assert data["discount_amount"] == 36.7
    assert data["currency_symbol"] == "AED"
    
    # Clean up
    client.delete(f"/coupons/{coupon_id}", headers={"Authorization": f"Bearer {admin_token}"})
