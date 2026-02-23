#!/usr/bin/env python3
"""
Check payment and order status to verify webhook updates.

This shows if Stripe webhooks are successfully updating payment status.

Usage:
  python3 scripts/check_payment_status.py [payment_intent_id]
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.payment import Payment
from app.models.order import Order
from sqlalchemy import desc


def check_payment_status(payment_intent_id=None):
    """Check payment status in database"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("PAYMENT STATUS CHECK")
        print("=" * 80)
        print()
        
        if payment_intent_id:
            # Check specific payment
            payment = db.query(Payment).filter(
                Payment.stripe_payment_intent_id == payment_intent_id
            ).first()
            
            if not payment:
                print(f"❌ Payment not found for PaymentIntent: {payment_intent_id}")
                return
            
            payments = [payment]
        else:
            # Show recent payments
            payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(10).all()
            print(f"Showing {len(payments)} most recent payments:")
            print()
        
        for p in payments:
            print("-" * 80)
            print(f"Payment ID: {p.id}")
            print(f"Stripe PaymentIntent: {p.stripe_payment_intent_id}")
            print(f"Status: {p.status}")
            print(f"Amount: {p.amount} {p.currency}")
            print(f"Created: {p.created_at}")
            print(f"Completed: {p.completed_at or 'Not completed'}")
            
            # Check order
            order = db.query(Order).filter(Order.id == p.order_id).first()
            if order:
                print(f"\nOrder ID: {order.id}")
                print(f"Order Status: {order.status}")
                print(f"Payment State: {order.payment_state or 'N/A'}")
                print(f"Total Amount: {order.total_amount}")
                
                # Check if coupons were added
                from app.models.user_coupon import UserCoupon
                user_coupons = db.query(UserCoupon).filter(
                    UserCoupon.user_id == order.user_id
                ).count()
                print(f"User has {user_coupons} coupons in wallet")
            
            # Check webhook metadata
            if p.payment_metadata:
                print(f"\nMetadata:")
                if 'stripe_event_id' in p.payment_metadata:
                    print(f"  Webhook Event ID: {p.payment_metadata['stripe_event_id']}")
                if 'failure_reason' in p.payment_metadata:
                    print(f"  Failure Reason: {p.payment_metadata['failure_reason']}")
            
            print()
        
        print("=" * 80)
        print("STATUS MEANINGS:")
        print("=" * 80)
        print("Payment Status:")
        print("  • pending         - Payment created, waiting for completion")
        print("  • succeeded       - ✓ Payment successful (webhook received)")
        print("  • failed          - ✗ Payment failed")
        print("  • cancelled       - Payment cancelled")
        print("  • processing      - Payment processing (bank transfer)")
        print()
        print("Order Status:")
        print("  • pending_payment - Waiting for payment")
        print("  • paid            - ✓ Payment successful, coupons added to wallet")
        print("  • failed          - Payment failed")
        print("  • cancelled       - Order cancelled")
        print()
        print("If payment status is 'succeeded' and order status is 'paid',")
        print("the webhook is working correctly!")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    pi_id = sys.argv[1] if len(sys.argv) > 1 else None
    check_payment_status(pi_id)
