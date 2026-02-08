
from sqlalchemy.orm import Session
from app.schemas.external_payment import ExternalPaymentRequest, ExternalPaymentResponse
from app.models.user import User
from app.models.order import Order
from app.services.stripe.payment_service import StripePaymentService
from app.services.stripe.token_service import PaymentTokenService
from app.utils.security import get_password_hash
import secrets
import string
import os
import uuid

class ExternalPaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.stripe_service = StripePaymentService(db)
        self.token_service = PaymentTokenService(db)
        self.payment_ui_domain = os.getenv("PAYMENT_UI_DOMAIN", "https://payment.vouchergalaxy.com")

    def _generate_random_password(self, length=12):
        chars = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(chars) for _ in range(length))

    def _get_or_create_user(self, request: ExternalPaymentRequest) -> tuple[User, str]:
        """
        Find existing user by phone or create a shadow user.
        Returns (User, status_string)
        """
        user = self.db.query(User).filter(User.phone_number == request.phone_number).first()
        
        if user:
            return user, "existing"
        
        # Create Shadow User
        raw_password = self._generate_random_password()
        full_name = f"{request.first_name} {request.second_name}".strip() if request.first_name else "Guest User"
        
        new_user = User(
            phone_number=request.phone_number,
            full_name=full_name,
            hashed_password=get_password_hash(raw_password),
            role="USER",
            is_active=True
            # Note: We don't verify shadow users immediately
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user, "created"

    def process_payment_request(self, request: ExternalPaymentRequest) -> ExternalPaymentResponse:
        # 1. Resolve User
        user, user_status = self._get_or_create_user(request)
        
        # 2. Create Pending Order
        # Note: External orders might not have items initially, or we treat the amount as a direct charge.
        # Since Order usually needs items, we might need to handle this. 
        # For now, we create an order without items, just `total_amount`.
        # The schema supports this as `items` is a relationship, not strictly required for insert if logic allows.
        new_order = Order(
            user_id=user.id,
            total_amount=float(request.amount),
            status="pending",
            payment_state="awaiting_payment",
            payment_method="stripe",
            webhook_url=str(request.webhook_url) if request.webhook_url else None
        )
        self.db.add(new_order)
        self.db.commit()
        self.db.refresh(new_order)
        
        # 3. Create Stripe PaymentIntent
        metadata = {
            "reference_id": request.reference_id,
            "source": "external_api",
            "user_phone": request.phone_number
        }
        # Amount in cents
        amount_cents = int(request.amount * 100)
        
        # This creates Payment record and updates Order
        self.stripe_service.create_payment_intent(
            order_id=new_order.id,
            amount=amount_cents,
            currency=request.currency,
            metadata=metadata
        )
        
        # Refresh order to get the stripe_payment_intent_id populated
        self.db.refresh(new_order)
        
        # 4. Generate Payment Token
        token = self.token_service.generate_payment_token(
            order_id=new_order.id,
            payment_intent_id=new_order.stripe_payment_intent_id,
            site_origin=str(request.return_url) if request.return_url else "external_api"
        )
        
        # 5. Construct URL
        base_url = f"{self.payment_ui_domain}/pay"
        payment_url = f"{base_url}?token={token.token}"
        if request.return_url:
            payment_url += f"&return_url={request.return_url}"
            
        return ExternalPaymentResponse(
            payment_url=payment_url,
            order_id=new_order.id,
            user_status=user_status,
            amount=request.amount,
            currency=request.currency
        )
