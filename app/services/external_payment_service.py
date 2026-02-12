
from sqlalchemy.orm import Session
from app.schemas.external_payment import (
    ExternalPaymentRequest, 
    ExternalPaymentResponse,
    ExternalPaymentStatusResponse
)
from app.models.user import User
from app.models.order import Order
from app.services.stripe.payment_service import StripePaymentService
from app.services.stripe.token_service import PaymentTokenService
from app.utils.security import get_password_hash
import secrets
import string
import os
import uuid
from sqlalchemy import func

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
        # 0. Idempotency Check
        existing_order = self.db.query(Order).filter(Order.reference_id == request.reference_id).first()
        if existing_order:
            # If order exists, return existing payment link logic (simplified for now)
            # In a real scenario, we might want to check status, etc.
            # Regenerate token for the existing order
            user = self.db.query(User).get(existing_order.user_id)
            user_status = "existing"
            
            # Check if payment intent exists
            if not existing_order.stripe_payment_intent_id:
                # Should not happen if flow completed previously, but safety check
                pass 
                
            token = self.token_service.generate_payment_token(
                order_id=existing_order.id,
                payment_intent_id=existing_order.stripe_payment_intent_id,
                site_origin=str(request.return_url) if request.return_url else "external_api"
            )
            
            base_url = f"{self.payment_ui_domain}/pay"
            payment_url = f"{base_url}?token={token.token}"
            if request.return_url:
                payment_url += f"&return_url={request.return_url}"
                
            return ExternalPaymentResponse(
                payment_url=payment_url,
                order_id=existing_order.id,
                user_status=user_status,
                amount=existing_order.total_amount,
                currency=request.currency # Assuming same currency
            )

        # 1. Resolve User
        user, user_status = self._get_or_create_user(request)
        
        # 2. Create Pending Order
        new_order = Order(
            user_id=user.id,
            total_amount=float(request.amount),
            status="pending",
            payment_state="awaiting_payment",
            payment_method="stripe",
            webhook_url=str(request.webhook_url) if request.webhook_url else None,
            reference_id=request.reference_id
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
    
    def get_payment_status_by_reference(self, reference_id: str) -> ExternalPaymentStatusResponse:
        """
        Get payment status by external reference ID.
        """
        # Query Order directly by reference_id
        order = self.db.query(Order).filter(Order.reference_id == reference_id).first()
        
        if not order:
            return None
            
        # Get associated payment
        from app.models.payment import Payment
        payment = self.db.query(Payment).filter(Payment.order_id == order.id).first()
        
        if not payment:
            # Order exists but no payment record yet (rare but possible if step 3 failed)
            return ExternalPaymentStatusResponse(
                reference_id=reference_id,
                status="pending",
                amount=order.total_amount,
                currency="USD", # Default fallback if no payment record
                created_at=order.created_at,
                order_id=order.id
            )

        # Map internal status to external status
        status_map = {
            "succeeded": "success",
            "initiated": "pending",
        }
        external_status = status_map.get(payment.status, payment.status)
            
        return ExternalPaymentStatusResponse(
            reference_id=reference_id,
            status=external_status,
            amount=payment.amount / 100.0,
            currency=payment.currency,
            created_at=payment.created_at,
            order_id=payment.order_id
        )
