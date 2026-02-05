"""
Stripe Webhook Endpoint

Handles incoming Stripe webhook events with signature verification.
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.stripe.webhook_service import StripeWebhookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Verifies the webhook signature and processes payment events.
    This endpoint should be configured in the Stripe Dashboard.
    
    Handled events:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - payment_intent.canceled
    - payment_intent.processing
    """
    # Get raw body for signature verification
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    if not sig_header:
        logger.warning("Webhook received without Stripe-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )
    
    webhook_service = StripeWebhookService(db)
    
    try:
        # Verify signature and construct event
        event = webhook_service.verify_webhook_signature(payload, sig_header)
        
        # Process the event
        result = webhook_service.handle_webhook_event(event)
        
        logger.info(f"Webhook processed: {event.get('type')} - {result.get('status')}")
        
        return {"received": True, "result": result}
        
    except ValueError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Still return 200 to prevent Stripe retries for non-retryable errors
        # Only raise HTTP error for verification failures
        return {"received": True, "error": str(e)}
