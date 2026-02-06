
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
import os
import logging
import hmac
import hashlib
import json

from app.database import get_db
from app.schemas.external_payment import ExternalPaymentRequest, ExternalPaymentResponse
from app.services.external_payment_service import ExternalPaymentService
from app.middleware.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

# The Key is now treated as a Secret for signing
EXTERNAL_API_SECRET = os.getenv("EXTERNAL_API_KEY")

async def verify_signature(request: Request, x_signature: str = Header(..., description="HMAC-SHA256 Signature")):
    if not EXTERNAL_API_SECRET:
         logger.error("EXTERNAL_API_KEY not configured on server")
         raise HTTPException(status_code=500, detail="Server configuration error")
    
    # Read the body carefully
    body_bytes = await request.body()
    
    # Compute HMAC-SHA256
    expected_signature = hmac.new(
        EXTERNAL_API_SECRET.encode(),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Compare secure (timing-attack resistant)
    if not hmac.compare_digest(expected_signature, x_signature):
        logger.warning("Invalid Signature attempt on External Payment API")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Signature"
        )
    return x_signature

@router.post("/payment-link", response_model=ExternalPaymentResponse)
@limiter.limit("60/minute")
async def create_payment_link(
    request: Request,
    payload: ExternalPaymentRequest,
    db: Session = Depends(get_db),
    signature: str = Depends(verify_signature)
):
    """
    Generate a payment link securely using HMAC Signature.
    """
    try:
        service = ExternalPaymentService(db)
        return service.process_payment_request(payload)
    except Exception as e:
        logger.error(f"Error generating payment link: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
