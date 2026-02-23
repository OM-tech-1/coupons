# Payment Webhook Fix - Coupon Wallet Integration

## Problem

Previously, coupons were being added to the user's wallet immediately when an order was created, regardless of payment status. This meant:

- Users could get coupons even if their Stripe payment failed
- Coupons appeared in wallet before payment was confirmed
- No proper synchronization between payment status and coupon delivery

## Solution

Coupons are now only added to the user's wallet when payment is successfully confirmed through the Stripe webhook.

## Changes Made

### 1. Order Service (`app/services/order_service.py`)

**Before:**
```python
# Coupons were added immediately for ALL orders
for c_id in coupons_to_grant:
    user_coupon = UserCoupon(user_id=user_id, coupon_id=c_id)
    db.add(user_coupon)
```

**After:**
```python
# Coupons only added if payment is already completed (free or non-Stripe)
if order.status == "paid":
    for c_id in coupons_to_grant:
        user_coupon = UserCoupon(user_id=user_id, coupon_id=c_id)
        db.add(user_coupon)
```

### 2. Webhook Service (`app/services/stripe/webhook_service.py`)

Added logic to grant coupons when `payment_intent.succeeded` webhook is received:

```python
def _handle_payment_succeeded(self, payment_intent: dict, event_id: str) -> dict:
    # ... payment status update ...
    
    # Add coupons to user's wallet now that payment succeeded
    for item in order.items:
        coupons_to_grant = []
        
        if item.coupon_id:
            coupons_to_grant.append(item.coupon_id)
        elif item.package_id and item.package:
            # Grant all coupons in the package
            coupons_to_grant.extend([c.coupon_id for c in item.package.coupon_associations])
        
        # Add each coupon to user's wallet
        for coupon_id in coupons_to_grant:
            existing_claim = self.db.query(UserCoupon).filter(
                UserCoupon.user_id == order.user_id,
                UserCoupon.coupon_id == coupon_id
            ).first()
            
            if not existing_claim:
                user_coupon = UserCoupon(
                    user_id=order.user_id,
                    coupon_id=coupon_id
                )
                self.db.add(user_coupon)
```

## Payment Flow

### Stripe Payment Flow - Regular Checkout (Async)

1. User adds items to cart
2. User initiates checkout with `payment_method="stripe"`
3. Order created with `status="pending_payment"`
4. Stripe PaymentIntent created
5. User completes payment on Stripe
6. **Stripe webhook fires** → `payment_intent.succeeded`
7. Webhook handler:
   - Updates order status to `"paid"`
   - Updates payment status to `"succeeded"`
   - **Adds coupons to user's wallet**
   - Increments coupon usage count
   - Sends outbound webhook (if configured)

### Stripe Payment Flow - External API (Async)

1. External system calls `/api/v1/external/payment-link` with HMAC signature
2. User created/retrieved, order created with `status="pending"`
3. Stripe PaymentIntent created
4. Payment link returned to external system
5. User completes payment on Stripe
6. **Stripe webhook fires** → `payment_intent.succeeded`
7. Webhook handler:
   - Updates order status to `"paid"`
   - Updates payment status to `"succeeded"`
   - **Adds coupons to user's wallet** (if order has items)
   - Sends outbound webhook to external system (if configured)

### Non-Stripe Payment Flow (Sync)

1. User adds items to cart
2. User initiates checkout with `payment_method="mock"` (or free coupons)
3. Payment processed immediately
4. Order created with `status="paid"`
5. **Coupons added to wallet immediately** (since payment already succeeded)
6. Cart cleared

## Webhook Configuration

To ensure webhooks work properly:

1. **Set webhook secret in environment:**
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret
   ```

2. **Configure webhook in Stripe Dashboard:**
   - URL: `https://api.vouchergalaxy.com/webhooks/stripe`
   - Events to send:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `payment_intent.canceled`
     - `payment_intent.processing`

3. **For CI/CD:**
   - Add `STRIPE_WEBHOOK_SECRET_TEST` to GitHub secrets for test mode
   - Add `STRIPE_WEBHOOK_SECRET` to GitHub secrets for production mode

## Testing

### Test with Mock Payment (Immediate)
```bash
POST /orders/checkout
{
  "payment_method": "mock"
}
```
Coupons appear in wallet immediately.

### Test with Stripe Payment (Webhook)
```bash
POST /orders/checkout
{
  "payment_method": "stripe"
}
```
Coupons appear in wallet only after:
1. User completes payment
2. Stripe webhook is received and processed

### Simulate Webhook Locally
```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

## Idempotency

The webhook handler includes idempotency checks:
- Won't add duplicate coupons if webhook is received multiple times
- Won't process already-succeeded payments
- Safe to retry webhook delivery

## Error Handling

If webhook fails:
- Stripe automatically retries webhook delivery
- Payment status remains in intermediate state
- User won't receive coupons until webhook succeeds
- Admin can manually trigger webhook or grant coupons

## Migration Notes

For existing orders with `status="pending_payment"`:
- If payment actually succeeded, manually trigger webhook or update status
- Check Stripe Dashboard for actual payment status
- Consider running a migration script to sync status

## Related Files

- `app/services/order_service.py` - Order creation logic
- `app/services/stripe/webhook_service.py` - Webhook handling
- `app/api/stripe/webhooks.py` - Webhook endpoint
- `tests/test_purchase_flow.py` - Updated tests
