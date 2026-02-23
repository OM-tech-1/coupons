# Wallet Logic Analysis

## Current Implementation

### How Coupons Are Added to Wallet

Coupons are added to the `user_coupons` table in **THREE** scenarios:

#### 1. Manual Claiming (Not Used for Purchases)
**File:** `app/services/user_coupon_service.py`
```python
def claim_coupon(db: Session, user_id: UUID, coupon_id: UUID):
    # This is for free claiming, not purchases
    user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon_id)
    db.add(user_coupon)
```

#### 2. Free/Mock Payment (Immediate)
**File:** `app/services/order_service.py` (Line 86-97)
```python
# Only add coupons to wallet if payment is already completed
if order.status == "paid":  # ✅ Only when paid!
    for c_id in coupons_to_grant:
        user_coupon = UserCoupon(user_id=user_id, coupon_id=c_id)
        db.add(user_coupon)
```

**When this happens:**
- Free coupons (price = 0)
- Mock payment method (testing)
- Order status is immediately set to "paid"

#### 3. Stripe Payment Success (Via Webhook)
**File:** `app/services/stripe/webhook_service.py` (Line 135-141)
```python
# In _handle_payment_succeeded
if order.status == "paid":  # After setting order.status = "paid"
    for coupon_id in coupons_to_grant:
        if not existing_claim:
            user_coupon = UserCoupon(user_id=order.user_id, coupon_id=coupon_id)
            self.db.add(user_coupon)
```

**When this happens:**
- Stripe sends `payment_intent.succeeded` webhook
- Order status is updated to "paid"
- Coupons are added to wallet

---

## Wallet Query Logic

### Current Wallet Endpoints

#### 1. GET /user/wallet (Summary)
**File:** `app/services/user_coupon_service.py`
```python
def get_wallet_summary(db: Session, user_id: UUID) -> dict:
    user_coupons = db.query(UserCoupon).filter(
        UserCoupon.user_id == user_id
    ).all()
    # Returns: total, active, used, expired counts
```

#### 2. GET /user/wallet/coupons (Detailed List)
**File:** `app/services/user_coupon_service.py`
```python
def get_wallet_coupons(db: Session, user_id: UUID) -> List[dict]:
    user_coupons = db.query(UserCoupon).filter(
        UserCoupon.user_id == user_id
    ).all()
    # Returns: full coupon details with status
```

#### 3. GET /user/coupons (All User Coupons)
**File:** `app/services/user_coupon_service.py`
```python
def get_user_coupons(db: Session, user_id: UUID) -> List[UserCoupon]:
    return db.query(UserCoupon).filter(
        UserCoupon.user_id == user_id
    ).all()
```

---

## ✅ Analysis Result

### The Logic is CORRECT!

The wallet queries are **already correct** because:

1. **Coupons are ONLY added to `user_coupons` table when payment succeeds**
   - Free/mock payments: Added immediately when order.status = "paid"
   - Stripe payments: Added via webhook when payment_intent.succeeded

2. **Wallet queries ONLY read from `user_coupons` table**
   - No JOIN with orders table
   - No filtering by order status
   - Simply shows what's in user_coupons

3. **Failed/Pending payments never add coupons**
   - Pending Stripe orders: status = "pending_payment" → coupons NOT added
   - Failed payments: webhook doesn't add coupons
   - Cancelled payments: webhook doesn't add coupons

---

## Potential Issues (If Wallet Shows Wrong Items)

### Issue 1: Webhook Not Processing
**Symptom:** User paid via Stripe but coupons not in wallet

**Cause:** Webhook not reaching server or failing

**Check:**
```bash
# Check if webhook secret is set
docker exec coupon-api-container printenv STRIPE_WEBHOOK_SECRET

# Check webhook logs
docker logs coupon-api-container | grep -i webhook

# Check order status
# Should be "paid" if webhook succeeded
```

**Fix:** Ensure webhook is configured and processing correctly

### Issue 2: Mock Payments in Production
**Symptom:** Test purchases showing in wallet

**Cause:** Using mock payment method in production

**Check:**
```sql
SELECT payment_method, status FROM orders WHERE user_id = 'xxx';
```

**Fix:** Ensure only Stripe payments are used in production

### Issue 3: Manual Claims
**Symptom:** Coupons in wallet that weren't purchased

**Cause:** Someone using the `/coupons/{id}/claim` endpoint

**Check:**
```sql
SELECT uc.*, o.id as order_id 
FROM user_coupons uc
LEFT JOIN order_items oi ON oi.coupon_id = uc.coupon_id
LEFT JOIN orders o ON o.id = oi.order_id AND o.user_id = uc.user_id
WHERE uc.user_id = 'xxx' AND o.id IS NULL;
```

**Fix:** Remove or restrict the claim endpoint if not needed

---

## Verification Query

To verify wallet shows only successfully purchased items:

```sql
-- Get all user coupons with their order status
SELECT 
    uc.id as user_coupon_id,
    uc.coupon_id,
    c.title as coupon_title,
    uc.claimed_at,
    o.id as order_id,
    o.status as order_status,
    o.payment_method,
    o.payment_state
FROM user_coupons uc
JOIN coupons c ON c.id = uc.coupon_id
LEFT JOIN order_items oi ON oi.coupon_id = uc.coupon_id
LEFT JOIN orders o ON o.id = oi.order_id AND o.user_id = uc.user_id
WHERE uc.user_id = 'USER_ID_HERE'
ORDER BY uc.claimed_at DESC;
```

**Expected Result:**
- All orders should have status = "paid"
- OR order_id is NULL (manual claim or package item)

---

## Recommendation

### The current implementation is CORRECT ✅

**No changes needed** to the wallet logic. The wallet already shows only:
1. Successfully purchased coupons (order.status = "paid")
2. Manually claimed coupons (if that feature is used)

### If Issues Persist

1. **Check webhook processing:**
   ```bash
   bash check_stripe_webhook_config.sh
   ```

2. **Verify order statuses:**
   ```sql
   SELECT status, payment_state, COUNT(*) 
   FROM orders 
   GROUP BY status, payment_state;
   ```

3. **Check for orphaned user_coupons:**
   ```sql
   SELECT COUNT(*) FROM user_coupons uc
   LEFT JOIN order_items oi ON oi.coupon_id = uc.coupon_id
   WHERE oi.id IS NULL;
   ```

---

## Summary

Your wallet logic is **already implemented correctly**. Coupons only appear in the wallet when:
- Payment succeeds (order.status = "paid")
- Webhook processes successfully (for Stripe payments)

If users are seeing incorrect items in their wallet, the issue is likely:
- Webhook not processing (configuration issue)
- Test/mock payments in production
- Manual claiming being used unexpectedly

The code does NOT need changes - focus on webhook configuration and testing!
