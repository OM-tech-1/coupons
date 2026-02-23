"""
Stripe Payments API Endpoints

Handles payment initialization, token validation, and status checks.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import os
import logging
import stripe

from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.stripe.payment import (
    PaymentInitRequest,
    PaymentInitResponse,
    TokenValidateRequest,
    TokenValidateResponse,
    PaymentStatusResponse,
)
from app.services.stripe.payment_service import StripePaymentService
from app.services.stripe.token_service import PaymentTokenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["stripe-payments"])

# Payment UI domain from environment
PAYMENT_UI_DOMAIN = os.getenv("PAYMENT_UI_DOMAIN", "https://payment.vouchergalaxy.com")


@router.post("/init", response_model=PaymentInitResponse)
async def initialize_payment(
    request: PaymentInitRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Initialize a payment for an order.
    
    Creates a Stripe PaymentIntent and returns a redirect URL
    with a short-lived token for the payment UI.
    """
    try:
        payment_service = StripePaymentService(db)
        token_service = PaymentTokenService(db)
        
        # Verify order exists and get amount from SOURCE OF TRUTH
        from app.models.order import Order
        order = db.query(Order).filter(Order.id == request.order_id).first()
        if not order:
             raise HTTPException(status_code=404, detail="Order not found")
        
        # Security: Allow Admins OR the Order Owner
        # We need to import UserRole properly, but for now strict ownership check is safer
        if order.user_id != current_user.id:
            # Check if admin (optional, but for now strict)
            # if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to pay for this order")
             
        # Convert float total_amount to integer cents using Decimal for precision
        from decimal import Decimal, ROUND_HALF_UP
        from app.services.coupon_service import CouponService
        
        # Use currency provided by frontend (the currency the user is viewing in)
        currency = request.currency.upper()
        
        final_amount_cents = 0
        
        # We need to fetch order items with coupon details
        if not order.items:
             # Reload with items if missing
             from sqlalchemy.orm import joinedload
             from app.models.order import OrderItem
             from app.models.coupon import Coupon
             from app.models.package import Package
             order = db.query(Order).options(
                 joinedload(Order.items).joinedload(OrderItem.coupon),
                 joinedload(Order.items).joinedload(OrderItem.package).joinedload(Package.coupon_associations)
             ).filter(Order.id == request.order_id).first()

        for item in order.items:
            coupon = item.coupon
            package = item.package
            
            if not coupon and not package:
                continue

            item_price = Decimal(0)

            if coupon:
                # 1. Pre-check Validity (Stock & Expiry)
                is_valid, reason = CouponService.is_valid(coupon)
                if not is_valid:
                     raise HTTPException(status_code=400, detail=f"Coupon '{coupon.code}' is not available: {reason}")
                
                if coupon.stock is not None and coupon.stock < item.quantity:
                     raise HTTPException(status_code=400, detail=f"Coupon '{coupon.code}' is out of stock (Requested: {item.quantity}, Available: {coupon.stock})")

                # 2. Get price for this currency (Using Decimal)
                if coupon.pricing and isinstance(coupon.pricing, dict):
                    if currency in coupon.pricing:
                         price_val = coupon.pricing[currency]
                         if isinstance(price_val, dict):
                             price_val = price_val.get("price", coupon.price)
                         item_price = Decimal(str(price_val))
                    else:
                         item_price = Decimal(str(coupon.price))
                else:
                     item_price = Decimal(str(coupon.price))
            
            elif package:
                # Package pricing: sum up all base prices of coupons inside the package for the given Currency
                base_sum = Decimal(0)
                for assoc in package.coupon_associations:
                    c = assoc.coupon
                    if not c: continue
                    
                    c_price = Decimal(0)
                    if c.pricing and isinstance(c.pricing, dict):
                        if currency in c.pricing:
                            pval = c.pricing[currency]
                            if isinstance(pval, dict):
                                pval = pval.get("price", c.price)
                            c_price = Decimal(str(pval))
                        else:
                            c_price = Decimal(str(c.price))
                    else:
                        c_price = Decimal(str(c.price))
                        
                    base_sum += c_price
                
                # Apply package discount
                discount = Decimal(str(package.discount or 0.0))
                multiplier = Decimal(1) - (discount / Decimal(100))
                item_price = base_sum * multiplier

            # Add to total: price * quantity * 100 (to cents)
            item_total_cents = (item_price * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            final_amount_cents += int(item_total_cents) * int(item.quantity)
            
        real_amount_cents = final_amount_cents

        if real_amount_cents < 50: # approx $0.50 check
             # If exact amount is 0 (free), we should handle it? 
             # Stripe requires > $0.50 usually.
             if real_amount_cents == 0:
                  # Free order? Should be handled by create_order, not here?
                  pass
             else:
                  raise HTTPException(status_code=400, detail="Order amount too small for payment processing (min $0.50)")
        
        # Create PaymentIntent
        payment = payment_service.create_payment_intent(
            order_id=request.order_id,
            amount=real_amount_cents,
            currency=currency,
            metadata=request.metadata,
        )
        
        # Generate short-lived token
        token = token_service.generate_payment_token(
            order_id=request.order_id,
            payment_intent_id=payment.stripe_payment_intent_id,
            site_origin=request.return_url,
        )
        
        # Build redirect URL
        redirect_url = f"{PAYMENT_UI_DOMAIN}/pay?token={token.token}"
        
        logger.info(f"Payment initialized for order {request.order_id}")
        
        return PaymentInitResponse(
            redirect_url=redirect_url,
            token=token.token,
            expires_at=token.expires_at,
            order_id=request.order_id,
            payment_intent_id=payment.stripe_payment_intent_id,
        )
        
    except ValueError as e:
        logger.error(f"Payment initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (400, 403, 404) as is
        raise
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {e}")
        # Return Stripe's user-friendly error message (e.g., "Amount must be at least...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.user_message or str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during payment init: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment initialization failed"
        )


@router.post("/validate-token", response_model=TokenValidateResponse)
async def validate_token(
    request: TokenValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a payment token and return Stripe client secret.
    
    Called by the payment UI to get the information needed
    to render Stripe Elements.
    """
    try:
        token_service = PaymentTokenService(db)
        payment_service = StripePaymentService(db)
        
        # Validate token
        token_data = token_service.validate_payment_token(request.token)
        
        return TokenValidateResponse(
            client_secret=token_data["client_secret"],
            amount=int(token_data["amount"]),
            currency=token_data["currency"],
            order_id=token_data["order_id"],
            publishable_key=payment_service.get_publishable_key(),
            return_url=token_data.get("return_url"),
        )
        
    except ValueError as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed"
        )


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the payment status for an order.
    
    Used by the main site to check payment completion.
    Requires authentication — only the order owner or an admin can check.
    """
    try:
        # Verify ownership
        from app.models.order import Order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        if order.user_id != current_user.id and current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this payment"
            )

        payment_service = StripePaymentService(db)
        
        payment = payment_service.get_payment_by_order(order_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No payment found for order {order_id}"
            )
        
        return PaymentStatusResponse(
            order_id=order_id,
            status=payment.status,
            amount=int(payment.amount),
            currency=payment.currency,
            paid_at=payment.completed_at,
            gateway=payment.gateway,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment status"
        )


@router.post("/mark-token-used")
async def mark_token_used(
    request: TokenValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a payment token as used.
    
    Called after successful payment confirmation to prevent token reuse.
    """
    try:
        token_service = PaymentTokenService(db)
        success = token_service.mark_token_used(request.token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        return {"status": "success", "message": "Token marked as used"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking token as used: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark token as used"
        )
