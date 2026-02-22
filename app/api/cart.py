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
    if item.package_id:
        cart_item, message = CartService.add_package_to_cart(
            db, current_user.id, item.package_id, item.quantity
        )
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        return {"message": message, "package_id": str(item.package_id)}
    else:
        cart_item, message = CartService.add_to_cart(
            db, current_user.id, item.coupon_id, item.quantity
        )
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        return {"message": message, "coupon_id": str(item.coupon_id)}


@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = CartService.get_cart(db, current_user.id)

    total = sum(
        (item.coupon.price or 0) * item.quantity
        for item in items
        if item.coupon
    )

    return {
        "items": items,
        "total_items": sum(i.quantity for i in items),
        "total_amount": total,
    }


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    coupon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    CartService.clear_cart(db, current_user.id)
    return None
