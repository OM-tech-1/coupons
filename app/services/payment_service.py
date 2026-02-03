"""
Payment Service - Mock Implementation

This module provides a mock payment service that simulates payment processing.
Replace the MockPaymentGateway class with real payment gateway integrations
(e.g., Razorpay, Stripe) when ready for production.

To integrate a real payment gateway:
1. Create a new class that implements the same interface as MockPaymentGateway
2. Replace the MockPaymentGateway usage in process_payment function
3. Add necessary API keys to environment variables
"""

import uuid
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    payment_id: str
    message: str
    gateway: str


class MockPaymentGateway:
    """
    Mock payment gateway for testing purposes.
    Always returns successful payment.
    
    TODO: Replace with real payment gateway:
    - RazorpayGateway
    - StripeGateway
    """
    
    @staticmethod
    def create_payment(amount: float, currency: str = "INR", **kwargs) -> PaymentResult:
        """Create a mock payment - always succeeds"""
        payment_id = f"mock_pay_{uuid.uuid4().hex[:16]}"
        return PaymentResult(
            success=True,
            payment_id=payment_id,
            message="Payment successful (mock)",
            gateway="mock"
        )
    
    @staticmethod
    def verify_payment(payment_id: str, **kwargs) -> Tuple[bool, str]:
        """Verify a mock payment - always succeeds"""
        if payment_id.startswith("mock_pay_"):
            return True, "Payment verified (mock)"
        return False, "Invalid payment ID"
    
    @staticmethod
    def refund_payment(payment_id: str, amount: float) -> Tuple[bool, str]:
        """Refund a mock payment"""
        return True, f"Refund processed for {amount} (mock)"


# ============================================================
# PLACEHOLDER FOR REAL PAYMENT GATEWAYS
# ============================================================

class RazorpayGateway:
    """
    TODO: Implement Razorpay integration
    
    Required environment variables:
    - RAZORPAY_KEY_ID
    - RAZORPAY_KEY_SECRET
    
    Example:
    import razorpay
    client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
    """
    pass


class StripeGateway:
    """
    TODO: Implement Stripe integration
    
    Required environment variables:
    - STRIPE_SECRET_KEY
    - STRIPE_PUBLISHABLE_KEY
    
    Example:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    """
    pass


# ============================================================
# PAYMENT SERVICE - Main Entry Point
# ============================================================

def process_payment(amount: float, method: str = "mock", **kwargs) -> PaymentResult:
    """
    Process a payment using the specified method.
    
    Args:
        amount: Amount to charge
        method: Payment method (mock, razorpay, stripe)
        **kwargs: Additional payment parameters
    
    Returns:
        PaymentResult with success status and payment ID
    """
    if method == "mock":
        gateway = MockPaymentGateway()
    elif method == "razorpay":
        # TODO: Replace with RazorpayGateway when implemented
        gateway = MockPaymentGateway()
    elif method == "stripe":
        # TODO: Replace with StripeGateway when implemented
        gateway = MockPaymentGateway()
    else:
        return PaymentResult(
            success=False,
            payment_id="",
            message=f"Unknown payment method: {method}",
            gateway=method
        )
    
    return gateway.create_payment(amount, **kwargs)


def verify_payment(payment_id: str, method: str = "mock", **kwargs) -> Tuple[bool, str]:
    """Verify a payment"""
    if method == "mock":
        return MockPaymentGateway.verify_payment(payment_id, **kwargs)
    # TODO: Add verification for other gateways
    return MockPaymentGateway.verify_payment(payment_id, **kwargs)
