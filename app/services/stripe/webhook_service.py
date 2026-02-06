"""
Stripe Webhook Service

Handles webhook signature verification and event processing
with idempotency guarantees.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.utils.stripe_client import get_stripe_client, get_stripe_config
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order

logger = logging.getLogger(__name__)


class StripeWebhookService:
    """Service for processing Stripe webhooks"""

    def __init__(self, db: Session):
        self.db = db
        self.stripe = get_stripe_client()
        self.config = get_stripe_config()

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> dict:
        """
        Verify webhook signature and construct event.
        
        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value
            
        Returns:
            Verified Stripe event object
            
        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = self.stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.config.webhook_secret
            )
            return event
        except self.stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook construction failed: {e}")
            raise ValueError(f"Webhook error: {e}")

    def handle_webhook_event(self, event: dict) -> dict:
        """
        Route webhook event to appropriate handler.
        
        Args:
            event: Verified Stripe event
            
        Returns:
            Dict with processing result
        """
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})
        event_id = event.get("id")
        
        logger.info(f"Processing webhook event: {event_type} (ID: {event_id})")
        
        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "payment_intent.canceled": self._handle_payment_canceled,
            "payment_intent.processing": self._handle_payment_processing,
        }
        
        handler = handlers.get(event_type)
        
        if handler:
            return handler(event_data, event_id)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    def _handle_payment_succeeded(self, payment_intent: dict, event_id: str) -> dict:
        """Handle successful payment"""
        pi_id = payment_intent.get("id")
        
        payment = self._get_payment_by_intent(pi_id)
        if not payment:
            logger.warning(f"Payment not found for PaymentIntent: {pi_id}")
            return {"status": "not_found", "payment_intent_id": pi_id}
        
        # Idempotency check - if already succeeded, skip
        if payment.status == PaymentStatus.SUCCEEDED.value:
            logger.info(f"Payment {payment.id} already marked as succeeded (idempotent)")
            return {"status": "already_processed", "payment_id": str(payment.id)}
        
        # Update payment
        payment.status = PaymentStatus.SUCCEEDED.value
        payment.completed_at = datetime.utcnow()
        payment.payment_metadata = payment.payment_metadata or {}
        payment.payment_metadata["stripe_event_id"] = event_id
        
        # Update order
        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = "paid"
            order.payment_state = "payment_completed"
        
        self.db.commit()
        
        logger.info(f"Payment {payment.id} marked as succeeded")
        
        # Dispatch Outbound Webhook
        self._send_outbound_webhook(order, "success")
        
        return {
            "status": "success",
            "payment_id": str(payment.id),
            "order_id": str(payment.order_id),
        }

    def _handle_payment_failed(self, payment_intent: dict, event_id: str) -> dict:
        """Handle failed payment"""
        pi_id = payment_intent.get("id")
        
        payment = self._get_payment_by_intent(pi_id)
        if not payment:
            logger.warning(f"Payment not found for PaymentIntent: {pi_id}")
            return {"status": "not_found", "payment_intent_id": pi_id}
        
        # Idempotency check
        if payment.status == PaymentStatus.FAILED.value:
            logger.info(f"Payment {payment.id} already marked as failed (idempotent)")
            return {"status": "already_processed", "payment_id": str(payment.id)}
        
        # Get failure reason
        last_error = payment_intent.get("last_payment_error", {})
        failure_reason = last_error.get("message", "Payment failed")
        
        # Update payment
        payment.status = PaymentStatus.FAILED.value
        payment.completed_at = datetime.utcnow()
        payment.payment_metadata = payment.payment_metadata or {}
        payment.payment_metadata["stripe_event_id"] = event_id
        payment.payment_metadata["failure_reason"] = failure_reason
        
        # Update order
        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = "failed"
            order.payment_state = "payment_failed"
        
        self.db.commit()
        
        logger.info(f"Payment {payment.id} marked as failed: {failure_reason}")
        
        # Dispatch Outbound Webhook
        self._send_outbound_webhook(order, "failed", failure_reason=failure_reason)
        
        return {
            "status": "success",
            "payment_id": str(payment.id),
            "order_id": str(payment.order_id),
            "failure_reason": failure_reason,
        }

    def _handle_payment_canceled(self, payment_intent: dict, event_id: str) -> dict:
        """Handle cancelled payment"""
        pi_id = payment_intent.get("id")
        
        payment = self._get_payment_by_intent(pi_id)
        if not payment:
            return {"status": "not_found", "payment_intent_id": pi_id}
        
        if payment.status == PaymentStatus.CANCELLED.value:
            return {"status": "already_processed", "payment_id": str(payment.id)}
        
        payment.status = PaymentStatus.CANCELLED.value
        payment.completed_at = datetime.utcnow()
        
        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = "cancelled"
            order.payment_state = "payment_cancelled"
        
        self.db.commit()
        
        return {"status": "success", "payment_id": str(payment.id)}

    def _handle_payment_processing(self, payment_intent: dict, event_id: str) -> dict:
        """Handle payment processing (e.g., bank transfers)"""
        pi_id = payment_intent.get("id")
        
        payment = self._get_payment_by_intent(pi_id)
        if not payment:
            return {"status": "not_found", "payment_intent_id": pi_id}
        
        if payment.status == PaymentStatus.PROCESSING.value:
            return {"status": "already_processed", "payment_id": str(payment.id)}
        
        payment.status = PaymentStatus.PROCESSING.value
        
        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.payment_state = "payment_processing"
        
        self.db.commit()
        
        return {"status": "success", "payment_id": str(payment.id)}

    def _send_outbound_webhook(self, order: Order, status: str, failure_reason: str = None):
        """
        Send a notification to the external system's webhook_url if configured.
        Uses HMAC signature for security.
        """
        if not order.webhook_url:
            return

        try:
            import requests # Lazy import
            import hmac
            import hashlib
            import json
            import os
            
            secret = os.getenv("EXTERNAL_API_KEY")
            if not secret:
                logger.warning("Cannot send outbound webhook: EXTERNAL_API_KEY not configured")
                return

            payload = {
                "order_id": str(order.id),
                "status": status,
                "amount": order.total_amount,
                "currency": "USD", # Default or from order
                "payment_id": order.stripe_payment_intent_id,
                "failure_reason": failure_reason
                # Add reference_id if available (stored in payment metadata)
            }
            
            # Serialize
            body_json = json.dumps(payload, separators=(',', ':'))
            
            # Sign
            signature = hmac.new(secret.encode(), body_json.encode(), hashlib.sha256).hexdigest()
            
            headers = {
                "x-signature": signature,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Dispatching outbound webhook to {order.webhook_url}")
            
            # Send with timeout (fire and forget pattern ideally, but here synchronous with short timeout)
            # In production, use BackgroundTasks
            requests.post(order.webhook_url, data=body_json, headers=headers, timeout=5)
            
        except Exception as e:
            logger.error(f"Failed to send outbound webhook: {e}")

    def _get_payment_by_intent(self, payment_intent_id: str):
        """Get payment by Stripe PaymentIntent ID"""
        return self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()
