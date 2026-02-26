import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine
from sqlalchemy.orm import Session

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def admin_token(db):
    from app.models.user import User
    from passlib.context import CryptContext
    from app.utils.jwt import create_access_token
    import uuid
    
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.phone_number == "+918943657095").first()
    
    if existing_admin:
        return create_access_token({"sub": str(existing_admin.id)})
    
    # Create new admin with unique phone number
    unique_phone = f"+91894365709{uuid.uuid4().hex[:1]}"
    admin = User(
        phone_number=unique_phone,
        hashed_password=pwd_context.hash("8943657095"),
        role="ADMIN",
        is_active=True
    )
    db.add(admin)
    db.commit()
    
    return create_access_token({"sub": str(admin.id)})


class TestContactModule:
    
    def test_submit_contact_message(self, db):
        """Test submitting a contact message (public endpoint)"""
        response = client.post("/contact/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Need help with coupon",
            "message": "I cannot redeem my coupon code. Please help."
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_submit_contact_invalid_email(self, db):
        """Test validation for invalid email"""
        response = client.post("/contact/", json={
            "name": "John Doe",
            "email": "invalid-email",
            "subject": "Test subject",
            "message": "Test message here"
        })
        
        assert response.status_code == 422
    
    def test_submit_contact_short_message(self, db):
        """Test validation for message too short"""
        response = client.post("/contact/", json={
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test subject",
            "message": "Short"
        })
        
        assert response.status_code == 422
    
    def test_list_messages_admin_only(self, db, admin_token):
        """Test listing messages requires admin"""
        # Create a message first
        client.post("/contact/", json={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "subject": "Payment issue",
            "message": "My payment failed but money was deducted."
        })
        
        # Try without auth
        response = client.get("/contact/admin")
        assert response.status_code == 401
        
        # Try with admin auth
        response = client.get(
            "/contact/admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) >= 1
    
    def test_get_single_message(self, db, admin_token):
        """Test getting a specific message"""
        # Create a message
        response = client.post("/contact/", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test subject",
            "message": "This is a test message for verification."
        })
        
        message_id = response.json()["id"]
        
        # Get the message as admin
        response = client.get(
            f"/contact/admin/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id
        assert data["email"] == "test@example.com"
    
    def test_update_message_status(self, db, admin_token):
        """Test updating message status to resolved"""
        # Create a message
        response = client.post("/contact/", json={
            "name": "Support User",
            "email": "support@example.com",
            "subject": "Resolved issue",
            "message": "This issue has been resolved now."
        })
        
        message_id = response.json()["id"]
        
        # Update status to resolved
        response = client.patch(
            f"/contact/admin/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "resolved"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
    
    def test_filter_by_status(self, db, admin_token):
        """Test filtering messages by status"""
        # Create pending message
        client.post("/contact/", json={
            "name": "User 1",
            "email": "user1@example.com",
            "subject": "Pending issue",
            "message": "This is a pending message."
        })
        
        # Create and resolve another message
        response = client.post("/contact/", json={
            "name": "User 2",
            "email": "user2@example.com",
            "subject": "Resolved issue",
            "message": "This will be resolved."
        })
        message_id = response.json()["id"]
        
        client.patch(
            f"/contact/admin/{message_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "resolved"}
        )
        
        # Filter by pending
        response = client.get(
            "/contact/admin?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "pending" for item in data["items"])
    
    def test_search_messages(self, db, admin_token):
        """Test searching messages"""
        # Create message with specific subject
        client.post("/contact/", json={
            "name": "Search Test",
            "email": "search@example.com",
            "subject": "Unique search term xyz123",
            "message": "This message should be findable."
        })
        
        # Search for it
        response = client.get(
            "/contact/admin?search=xyz123",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("xyz123" in item["subject"] for item in data["items"])
