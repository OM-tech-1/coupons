from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.schemas.order import OrderResponse, CheckoutRequest
from app.services.order_service import OrderService

router = APIRouter()


@router.post("/checkout", response_model=OrderResponse)
def checkout(
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Checkout cart and create order with payment"""
    order, message = OrderService.create_order_from_cart(
        db, current_user.id, checkout_data.payment_method
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Determine and set currency
    currency_code = "USD"
    if current_user:
        currency_code = getattr(current_user, "context_currency", None) or get_currency_from_phone_code(current_user.phone_number)
    
    order.currency = currency_code
    order.currency_symbol = get_currency_symbol(currency_code)
    
    return order


from app.utils.currency import get_currency_from_phone_code, get_currency_symbol

@router.get("/", response_model=List[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's orders"""
    orders = OrderService.get_user_orders(db, current_user.id)
    
    # Apply currency to orders
    currency_code = "USD"
    if current_user:
        currency_code = getattr(current_user, "context_currency", None) or get_currency_from_phone_code(current_user.phone_number)
    
    symbol = get_currency_symbol(currency_code)
    
    for order in orders:
        order.currency = currency_code
        order.currency_symbol = symbol
        
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific order"""
    order = OrderService.get_order_by_id(db, order_id, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.get("/{order_id}/invoice")
def download_invoice(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download invoice PDF for an order"""
    order = OrderService.get_order_by_id(db, order_id, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Generate PDF
    from app.services.invoice_service import InvoiceService
    from fastapi.responses import StreamingResponse
    
    pdf_buffer = InvoiceService.generate_invoice_pdf(order, current_user)
    
    filename = f"invoice_{str(order.id)[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
