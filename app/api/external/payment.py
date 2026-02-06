
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import os
import logging

from app.database import get_db
from app.schemas.external_payment import ExternalPaymentRequest, ExternalPaymentResponse
from app.services.external_payment_service import ExternalPaymentService

router = APIRouter()
logger = logging.getLogger(__name__)

# Load API Key
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")

async def verify_api_key(x_api_key: str = Header(..., description="Secure API Key")):
    if not EXTERNAL_API_KEY:
         logger.error("EXTERNAL_API_KEY not configured on server")
         raise HTTPException(status_code=500, detail="Server configuration error")
    
    if x_api_key != EXTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

@router.post("/payment-link", response_model=ExternalPaymentResponse)
def create_payment_link(
    request: ExternalPaymentRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Generate a payment link for a user (existing or guest) via secure API Key.
    """
    try:
        service = ExternalPaymentService(db)
        return service.process_payment_request(request)
    except Exception as e:
        logger.error(f"Error generating payment link: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
