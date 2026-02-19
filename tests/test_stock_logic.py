import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon
from app.utils.security import get_current_user
from app.database import get_db

client = TestClient(app)

MOCK_USER_ID = "550e8400-e29b-41d4-a716-446655440001"
MOCK_ORDER_ID = "550e8400-e29b-41d4-a716-446655440099"

@pytest.fixture
def mock_db():
    return MagicMock()

def test_payment_init_out_of_stock(mock_db):
    """Test that payment init fails if coupon is out of stock"""
    
    # Mock current user
    mock_user = User(id=MOCK_USER_ID, phone_number="+15550000000", role="USER")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    with patch("app.services.stripe.payment_service.get_stripe_client") as mock_stripe_client:
        
        # Mock Coupon - OUT OF STOCK
        mock_coupon = Coupon(
            code="TEST",
            price=10.0, 
            stock=0, # No stock
            is_active=True
        )
        
        mock_item = OrderItem(quantity=1, coupon=mock_coupon)
        mock_item.coupon = mock_coupon
        
        mock_order = Order(id=MOCK_ORDER_ID, user_id=MOCK_USER_ID, total_amount=10.0, items=[mock_item])
        
        # Database Mocks
        def query_side_effect(model):
            mock_q = MagicMock()
            if model == Order:
                 mock_q.filter.return_value.first.return_value = mock_order
                 mock_q.options.return_value.filter.return_value.first.return_value = mock_order
            return mock_q
        
        mock_db.query.side_effect = query_side_effect

        response = client.post(
            "/payments/init",
            json={"order_id": MOCK_ORDER_ID, "return_url": "http://test.com"}
        )
        
        # Expect 400 Bad Request
        assert response.status_code == 400
        assert "out of stock" in response.json()["detail"]
    
    app.dependency_overrides = {}

def test_payment_init_stock_available(mock_db):
    """Test that payment init succeeds if stock is available"""
    
    # Mock current user
    mock_user = User(id=MOCK_USER_ID, phone_number="+15550000000", role="USER")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    with patch("app.services.stripe.payment_service.get_stripe_client") as mock_stripe_client:
        
        # Mock Stripe
        mock_stripe = MagicMock()
        mock_stripe_client.return_value = mock_stripe
        mock_stripe.PaymentIntent.create.return_value = MagicMock(id="pi_123", client_secret="secret")

        # Mock Coupon - IN STOCK
        mock_coupon = Coupon(
            code="TEST",
            price=10.0, 
            stock=5, 
            is_active=True
        )
        
        mock_item = OrderItem(quantity=2, coupon=mock_coupon) # Buying 2, Stock 5 OK
        mock_item.coupon = mock_coupon
        
        mock_order = Order(id=MOCK_ORDER_ID, user_id=MOCK_USER_ID, total_amount=20.0, items=[mock_item])
        
        # Database Mocks
        from app.models.payment import Payment
        def query_side_effect(model):
            mock_q = MagicMock()
            if model == Order:
                 mock_q.filter.return_value.first.return_value = mock_order
                 mock_q.options.return_value.filter.return_value.first.return_value = mock_order
            elif model == Payment:
                 mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect

        response = client.post(
            "/payments/init",
            json={"order_id": MOCK_ORDER_ID, "return_url": "http://test.com"}
        )
        
        # Expect 200 OK
        assert response.status_code == 200
        assert response.json()["payment_intent_id"] == "pi_123"
    
    app.dependency_overrides = {}
