"""
Stripe Webhook Endpoint

Handles incoming Stripe webhook events with signature verification.
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging
import json
from datetime import datetime

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
    
    # Log incoming webhook request
    timestamp = datetime.utcnow().isoformat()
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"[WEBHOOK] Incoming request at {timestamp}")
    logger.info(f"[WEBHOOK] Client IP: {client_ip}")
    logger.info(f"[WEBHOOK] Headers: {dict(request.headers)}")
    logger.info(f"[WEBHOOK] Payload size: {len(payload)} bytes")
    
    # Try to parse and log payload (safely)
    try:
        payload_json = json.loads(payload.decode('utf-8'))
        event_type = payload_json.get('type', 'unknown')
        event_id = payload_json.get('id', 'unknown')
        logger.info(f"[WEBHOOK] Event Type: {event_type}")
        logger.info(f"[WEBHOOK] Event ID: {event_id}")
        logger.info(f"[WEBHOOK] Full Payload: {json.dumps(payload_json, indent=2)}")
    except Exception as parse_error:
        logger.warning(f"[WEBHOOK] Could not parse payload as JSON: {parse_error}")
        logger.info(f"[WEBHOOK] Raw Payload: {payload.decode('utf-8', errors='replace')[:1000]}")
    
    if not sig_header:
        logger.warning("[WEBHOOK] Missing Stripe-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )
    
    logger.info(f"[WEBHOOK] Stripe-Signature present: {sig_header[:50]}...")
    
    webhook_service = StripeWebhookService(db)
    
    try:
        # Verify signature and construct event
        logger.info("[WEBHOOK] Verifying signature...")
        event = webhook_service.verify_webhook_signature(payload, sig_header)
        logger.info(f"[WEBHOOK] Signature verified successfully for event: {event.get('type')}")
        
        # Process the event
        logger.info(f"[WEBHOOK] Processing event: {event.get('type')} (ID: {event.get('id')})")
        result = webhook_service.handle_webhook_event(event)
        
        logger.info(f"[WEBHOOK] Event processed successfully: {event.get('type')} - Status: {result.get('status')}")
        
        return {"received": True, "result": result}
        
    except ValueError as e:
        logger.error(f"[WEBHOOK] Signature verification failed: {e}")
        logger.error(f"[WEBHOOK] Signature header: {sig_header}")
        logger.error(f"[WEBHOOK] Payload (first 500 chars): {payload.decode('utf-8', errors='replace')[:500]}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[WEBHOOK] Processing error: {e}", exc_info=True)
        logger.error(f"[WEBHOOK] Event that caused error: {event.get('type') if 'event' in locals() else 'unknown'}")
        # Still return 200 to prevent Stripe retries for non-retryable errors
        # Only raise HTTP error for verification failures
        return {"received": True, "error": str(e)}
