from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartResponse
from app.services.cart_service import CartService

router = APIRouter()


@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a coupon to cart"""
    cart_item, message = CartService.add_to_cart(
        db, current_user.id, item.coupon_id, item.quantity
    )
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {"message": message, "coupon_id": str(item.coupon_id)}


from app.utils.currency import get_currency_from_phone_code, get_currency_symbol
from app.services.coupon_service import CouponService

@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's cart"""
    items = CartService.get_cart(db, current_user.id)
    
    # Determine currency
    currency_code = "USD"
    if current_user:
        currency_code = getattr(current_user, "context_currency", None) or get_currency_from_phone_code(current_user.phone_number)
    
    # Apply currency to each item's coupon
    for item in items:
        if item.coupon:
            CouponService._apply_currency(item.coupon, currency_code)

    # Compute total from fetched items instead of a second DB query
    total = sum(
        (item.coupon.price or 0) * item.quantity
        for item in items
        if item.coupon
    )
    
    return {
        "items": items,
        "total_items": sum(i.quantity for i in items),
        "total_amount": total,
        "currency": currency_code,
        "currency_symbol": get_currency_symbol(currency_code)
    }


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a coupon from cart"""
    success = CartService.remove_from_cart(db, current_user.id, coupon_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not in cart"
        )
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all items from cart"""
    CartService.clear_cart(db, current_user.id)
    return None
