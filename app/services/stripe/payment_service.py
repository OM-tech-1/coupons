"""
Stripe Payment Service

Handles PaymentIntent creation, retrieval, and management.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from app.utils.stripe_client import get_stripe_client, get_stripe_config
from app.models.payment import Payment, PaymentStatus, PaymentGateway
from app.models.order import Order

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Service for Stripe payment operations"""

    def __init__(self, db: Session):
        self.db = db
        self.stripe = get_stripe_client()
        self.config = get_stripe_config()

    def create_payment_intent(
        self,
        order_id: UUID,
        amount: int,
        currency: str = "USD",
        metadata: Optional[dict] = None
    ) -> Payment:
        """
        Create a Stripe PaymentIntent and associated Payment record.
        
        Args:
            order_id: UUID of the order
            amount: Amount in smallest currency unit (cents for USD)
            currency: 3-letter currency code
            metadata: Optional metadata to attach to PaymentIntent
            
        Returns:
            Payment record with Stripe details
            
        Raises:
            ValueError: If order not found or already has payment
            stripe.error.StripeError: If Stripe API fails
        """
        # Verify order exists
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Check for existing payment
        existing_payment = self.db.query(Payment).filter(
            Payment.order_id == order_id
        ).first()
        
        if existing_payment and existing_payment.is_completed():
            raise ValueError(f"Order {order_id} already has a completed payment")
        
        # Note: We don't cancel old PaymentIntents to avoid 500-1000ms API call
        # Stripe automatically expires abandoned PaymentIntents after 24 hours

        # Prepare metadata
        pi_metadata = {
            "order_id": str(order_id),
            "integration": "vouchergalaxy",
        }
        if metadata:
            pi_metadata.update(metadata)

        # Create PaymentIntent
        payment_intent = self.stripe.PaymentIntent.create(
            amount=amount,
            currency=currency.lower(),
            metadata=pi_metadata,
            automatic_payment_methods={"enabled": True},
        )

        logger.info(f"Created PaymentIntent: {payment_intent.id}")

        # Create or update Payment record
        if existing_payment:
            existing_payment.stripe_payment_intent_id = payment_intent.id
            existing_payment.stripe_client_secret = payment_intent.client_secret
            existing_payment.amount = amount
            existing_payment.currency = currency.upper()
            existing_payment.status = PaymentStatus.PENDING.value
            existing_payment.payment_metadata = pi_metadata
            payment = existing_payment
        else:
            payment = Payment(
                order_id=order_id,
                stripe_payment_intent_id=payment_intent.id,
                stripe_client_secret=payment_intent.client_secret,
                amount=amount,
                currency=currency.upper(),
                status=PaymentStatus.PENDING.value,
                gateway=PaymentGateway.STRIPE.value,
                payment_metadata=pi_metadata,
            )
            self.db.add(payment)

        # Update order with payment intent reference
        order.stripe_payment_intent_id = payment_intent.id
        order.payment_state = "payment_initiated"
        order.payment_method = "stripe"

        self.db.commit()
        self.db.refresh(payment)

        return payment

    def retrieve_payment_intent(self, payment_intent_id: str) -> dict:
        """
        Retrieve a PaymentIntent from Stripe.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            
        Returns:
            PaymentIntent object from Stripe
        """
        return self.stripe.PaymentIntent.retrieve(payment_intent_id)

    def cancel_payment_intent(self, payment_intent_id: str) -> bool:
        """
        Cancel a PaymentIntent.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.stripe.PaymentIntent.cancel(payment_intent_id)
            
            # Update local payment record
            payment = self.db.query(Payment).filter(
                Payment.stripe_payment_intent_id == payment_intent_id
            ).first()
            
            if payment:
                payment.status = PaymentStatus.CANCELLED.value
                self.db.commit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to cancel PaymentIntent {payment_intent_id}: {e}")
            return False

    def get_payment_by_order(self, order_id: UUID) -> Optional[Payment]:
        """Get payment record for an order"""
        return self.db.query(Payment).filter(Payment.order_id == order_id).first()

    def get_payment_by_intent(self, payment_intent_id: str) -> Optional[Payment]:
        """Get payment record by Stripe PaymentIntent ID"""
        return self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

    def get_publishable_key(self) -> str:
        """Get Stripe publishable key for frontend"""
        return self.config.publishable_key
