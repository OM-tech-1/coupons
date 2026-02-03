from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Tuple

from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.models.user_coupon import UserCoupon
from app.services.cart_service import CartService
from app.services.payment_service import process_payment, PaymentResult


class OrderService:
    
    @staticmethod
    def create_order_from_cart(db: Session, user_id: UUID, payment_method: str = "mock") -> Tuple[Optional[Order], str]:
        """Create an order from user's cart and process payment"""
        # Get cart items
        cart_items = CartService.get_cart(db, user_id)
        if not cart_items:
            return None, "Cart is empty"
        
        # Calculate total
        total = CartService.get_cart_total(db, user_id)
        if total <= 0:
            # Free coupons - skip payment
            order = Order(
                user_id=user_id,
                total_amount=0,
                status="paid",
                payment_method="free"
            )
        else:
            # Process payment
            payment_result: PaymentResult = process_payment(total, method=payment_method)
            
            if not payment_result.success:
                return None, payment_result.message
            
            order = Order(
                user_id=user_id,
                total_amount=total,
                status="paid",
                payment_id=payment_result.payment_id,
                payment_method=payment_result.gateway
            )
        
        db.add(order)
        db.flush()  # Get order ID
        
        # Create order items and user coupons
        for cart_item in cart_items:
            # Add to order
            order_item = OrderItem(
                order_id=order.id,
                coupon_id=cart_item.coupon_id,
                quantity=cart_item.quantity,
                price=cart_item.coupon.price if cart_item.coupon else 0
            )
            db.add(order_item)
            
            # Add coupons to user's claimed list
            for _ in range(cart_item.quantity):
                user_coupon = UserCoupon(
                    user_id=user_id,
                    coupon_id=cart_item.coupon_id
                )
                db.add(user_coupon)
        
        # Clear cart
        CartService.clear_cart(db, user_id)
        
        db.commit()
        db.refresh(order)
        return order, "Order created successfully"

    @staticmethod
    def get_user_orders(db: Session, user_id: UUID) -> List[Order]:
        """Get all orders for a user"""
        return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order_by_id(db: Session, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Get an order by ID (must belong to user)"""
        return db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
