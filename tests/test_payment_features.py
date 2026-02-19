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

# Mock Data
MOCK_USER_ID = "550e8400-e29b-41d4-a716-446655440001"
MOCK_OTHER_USER_ID = "550e8400-e29b-41d4-a716-446655440002"
MOCK_ORDER_ID = "550e8400-e29b-41d4-a716-446655440099"

@pytest.fixture
def mock_db():
    return MagicMock()

def test_payment_init_security_wrong_user(mock_db):
    """Test that a user cannot pay for another user's order"""
    
    # Mock current user (Attacker)
    mock_attacker = User(id=MOCK_OTHER_USER_ID, phone_number="+15550000000", role="USER")
    app.dependency_overrides[get_current_user] = lambda: mock_attacker
    app.dependency_overrides[get_db] = lambda: mock_db
    
    try:
        mock_order = Order(id=MOCK_ORDER_ID, user_id=MOCK_USER_ID, total_amount=100.0)
        
        # Configure DB Query Side Effect
        def query_side_effect(model):
            mock_q = MagicMock()
            if model == Order:
                 mock_q.filter.return_value.first.return_value = mock_order
                 # Create a mock for the options chain: query().options().filter().first()
                 mock_q.options.return_value.filter.return_value.first.return_value = mock_order
            return mock_q
            
        mock_db.query.side_effect = query_side_effect
        
        response = client.post(
            "/payments/init",
            json={"order_id": MOCK_ORDER_ID, "return_url": "http://test.com"}
        )
        
        # Expect 403 Forbidden
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
    finally:
        app.dependency_overrides = {}

def test_payment_init_explicit_pricing_aed(mock_db):
    """Test that AED pricing is used when user is from UAE"""
    from app.models.payment import Payment
    
    # Mock current user (UAE User)
    mock_user = User(id=MOCK_USER_ID, phone_number="+971501234567", role="USER")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    
    with patch("app.services.stripe.payment_service.get_stripe_client") as mock_stripe_client:
        
        # Mock Stripe
        mock_stripe = MagicMock()
        mock_stripe_client.return_value = mock_stripe
        mock_stripe.PaymentIntent.create.return_value = MagicMock(id="pi_123", client_secret="secret")
        
        # Mock Data
        mock_coupon = Coupon(price=10.0, pricing={"AED": 50.0, "INR": 500.0})
        mock_item = OrderItem(quantity=2, coupon=mock_coupon)
        mock_item.coupon = mock_coupon # Explicitly set relationship for logic
        mock_order = Order(id=MOCK_ORDER_ID, user_id=MOCK_USER_ID, total_amount=20.0, items=[mock_item])
        
        # Configure DB Query Side Effect
        def query_side_effect(model):
            mock_q = MagicMock()
            if model == Order:
                 mock_q.filter.return_value.first.return_value = mock_order
                 mock_q.options.return_value.filter.return_value.first.return_value = mock_order
            elif model == Payment:
                 # Return None for existing payment check
                 mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        mock_db.query.side_effect = query_side_effect

        response = client.post(
            "/payments/init",
            json={"order_id": MOCK_ORDER_ID, "return_url": "http://test.com"}
        )
        
        # Validation
        assert response.status_code == 200
        
        # Check Stripe Call
        mock_stripe.PaymentIntent.create.assert_called_once()
        call_args = mock_stripe.PaymentIntent.create.call_args[1]
        
        assert call_args["amount"] == 10000
        assert call_args["currency"] == "aed"
    
    app.dependency_overrides = {}
