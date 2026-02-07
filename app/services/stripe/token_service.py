"""
Payment Token Service

Handles generation and validation of short-lived tokens for
secure cross-domain payment authentication.
"""
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
import os
import logging

from app.models.payment_token import PaymentToken
from app.models.payment import Payment
from app.models.order import Order

logger = logging.getLogger(__name__)

# Token secret from environment
TOKEN_SECRET = os.getenv("PAYMENT_TOKEN_SECRET", "change-me-in-production")
TOKEN_TTL_MINUTES = int(os.getenv("PAYMENT_TOKEN_TTL_MINUTES", "5"))


class PaymentTokenService:
    """Service for payment token operations"""

    def __init__(self, db: Session):
        self.db = db
        self.secret = TOKEN_SECRET
        self.ttl_minutes = TOKEN_TTL_MINUTES

    def generate_payment_token(
        self,
        order_id: UUID,
        payment_intent_id: str,
        site_origin: Optional[str] = None,
        ttl_minutes: Optional[int] = None
    ) -> PaymentToken:
        """
        Generate a short-lived token for payment authentication.
        
        Args:
            order_id: UUID of the order
            payment_intent_id: Stripe PaymentIntent ID
            site_origin: Optional origin site identifier
            ttl_minutes: Optional custom TTL (defaults to env config)
            
        Returns:
            PaymentToken record
        """
        ttl = ttl_minutes or self.ttl_minutes
        expires_at = datetime.utcnow() + timedelta(minutes=ttl)
        
        # Generate JWT token
        payload = {
            "order_id": str(order_id),
            "payment_intent_id": payment_intent_id,
            "site": site_origin or "vouchergalaxy",
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),  # Unique token ID
        }
        
        token_str = jwt.encode(payload, self.secret, algorithm="HS256")
        
        # Store token in database
        token = PaymentToken(
            token=token_str,
            order_id=order_id,
            payment_intent_id=payment_intent_id,
            expires_at=expires_at,
            site_origin=site_origin,
        )
        
        self.db.add(token)
        self.db.commit()
        # No need to refresh - we have all the data we need
        
        logger.info(f"Generated payment token for order {order_id}, expires at {expires_at}")
        
        return token

    def validate_payment_token(self, token_str: str) -> dict:
        """
        Validate a payment token and return payment details.
        
        Args:
            token_str: JWT token string
            
        Returns:
            Dict with payment details (order_id, payment_intent_id, client_secret)
            
        Raises:
            ValueError: If token is invalid, expired, or already used
        """
        # First decode JWT to get basic info
        try:
            payload = jwt.decode(token_str, self.secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
        
        # Look up token in database
        token_record = self.db.query(PaymentToken).filter(
            PaymentToken.token == token_str
        ).first()
        
        if not token_record:
            raise ValueError("Token not found")
        
        if token_record.is_used:
            raise ValueError("Token has already been used")
        
        if token_record.is_expired():
            raise ValueError("Token has expired")
        
        # Get the payment record
        payment = self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == token_record.payment_intent_id
        ).first()
        
        if not payment:
            raise ValueError("Payment not found for token")
        
        # Get order
        order = self.db.query(Order).filter(
            Order.id == token_record.order_id
        ).first()
        
        if not order:
            raise ValueError("Order not found for token")
        
        # Check if payment is already completed
        if payment.is_completed():
            raise ValueError(f"Payment already in terminal state: {payment.status}")
        
        logger.info(f"Validated token for order {token_record.order_id}")
        
        return {
            "order_id": str(token_record.order_id),
            "payment_intent_id": token_record.payment_intent_id,
            "client_secret": payment.stripe_client_secret,
            "amount": payment.amount,
            "currency": payment.currency,
            "order_total": order.total_amount,
            "return_url": token_record.site_origin,
        }

    def mark_token_used(self, token_str: str) -> bool:
        """
        Mark a token as used.
        
        Args:
            token_str: JWT token string
            
        Returns:
            True if marked successfully
        """
        token_record = self.db.query(PaymentToken).filter(
            PaymentToken.token == token_str
        ).first()
        
        if token_record:
            token_record.is_used = True
            token_record.used_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Marked token as used for order {token_record.order_id}")
            return True
            
        return False

    def cleanup_expired_tokens(self, older_than_hours: int = 24) -> int:
        """
        Clean up expired tokens older than specified hours.
        
        Args:
            older_than_hours: Delete tokens expired more than this many hours ago
            
        Returns:
            Number of tokens deleted
        """
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        deleted = self.db.query(PaymentToken).filter(
            PaymentToken.expires_at < cutoff
        ).delete()
        
        self.db.commit()
        logger.info(f"Cleaned up {deleted} expired tokens")
        
        return deleted
