from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List, Optional, Tuple

from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.models.coupon import Coupon
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
            if payment_method == "stripe":
                # Async payment flow - create pending order
                order = Order(
                    user_id=user_id,
                    total_amount=total,
                    status="pending_payment",
                    payment_method="stripe"
                )
            else:
                # Process payment (mock/synchronous)
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
        
        # Create order items
        for cart_item in cart_items:
            # Figure out price and coupons to grant
            order_item = OrderItem(
                order_id=order.id,
                coupon_id=cart_item.coupon_id,
                package_id=cart_item.package_id,
                quantity=cart_item.quantity,
                price=0.0
            )
            
            coupons_to_grant = []
            if cart_item.coupon:
                order_item.price = cart_item.coupon.price or 0.0
                coupons_to_grant.append(cart_item.coupon_id)
            elif cart_item.package:
                base_sum = sum(c.coupon.price for c in cart_item.package.coupon_associations if c.coupon and c.coupon.price)
                discount = cart_item.package.discount or 0.0
                order_item.price = base_sum * (1.0 - discount / 100.0)
                coupons_to_grant.extend([c.coupon_id for c in cart_item.package.coupon_associations])

            db.add(order_item)
            
            # Only add coupons to wallet if payment is already completed (free or non-Stripe)
            # For Stripe payments, coupons will be added via webhook when payment succeeds
            if order.status == "paid":
                for c_id in coupons_to_grant:
                    existing_claim = db.query(UserCoupon).filter(
                        UserCoupon.user_id == user_id,
                        UserCoupon.coupon_id == c_id
                    ).first()
                    if not existing_claim:
                        user_coupon = UserCoupon(
                            user_id=user_id,
                            coupon_id=c_id
                        )
                        db.add(user_coupon)
        
        # Clear cart
        CartService.clear_cart(db, user_id)
        
        db.commit()
        db.refresh(order)
        return order, "Order created successfully"

    @staticmethod
    def get_user_orders(db: Session, user_id: UUID) -> List[Order]:
        """Get all orders for a user with coupon and category details"""
        return db.query(Order).filter(
            Order.user_id == user_id
        ).options(
            joinedload(Order.items).joinedload(OrderItem.coupon).joinedload(Coupon.category),
            joinedload(Order.items).joinedload(OrderItem.package)
        ).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order_by_id(db: Session, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Get an order by ID (must belong to user) with coupon and category details"""
        return db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).options(
            joinedload(Order.items).joinedload(OrderItem.coupon).joinedload(Coupon.category),
            joinedload(Order.items).joinedload(OrderItem.package)
        ).first()
