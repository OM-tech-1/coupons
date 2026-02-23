# Stripe Webhook Implementation Review

## Comparison with Stripe Best Practices

I've reviewed your implementation against [Stripe's webhook documentation](https://docs.stripe.com/webhooks/quickstart) and best practices. Here's the analysis:

---

## ✅ What You're Doing RIGHT

### 1. ✅ Signature Verification (CRITICAL)
**Stripe Requirement:** Always validate the signature using the raw request body

**Your Implementation:**
```python
# app/api/stripe/webhooks.py
payload = await request.body()  # ✅ Raw body
sig_header = request.headers.get("Stripe-Signature")  # ✅ Correct header

# app/services/stripe/webhook_service.py
event = self.stripe.Webhook.construct_event(
    payload,
    sig_header,
    self.config.webhook_secret  # ✅ Using webhook secret
)
```

**Status:** ✅ PERFECT - You're using the official Stripe SDK method with raw body

### 2. ✅ Idempotency Handling
**Stripe Requirement:** Handle events idempotently, record event IDs to prevent duplicate processing

**Your Implementation:**
```python
# Check if already processed
if payment.status == PaymentStatus.SUCCEEDED.value:
    logger.info(f"Payment {payment.id} already marked as succeeded (idempotent)")
    return {"status": "already_processed", "payment_id": str(payment.id)}
```

**Status:** ✅ GOOD - You check payment status before processing

### 3. ✅ Event Type Routing
**Stripe Requirement:** Switch on event.type to handle different events

**Your Implementation:**
```python
handlers = {
    "payment_intent.succeeded": self._handle_payment_succeeded,
    "payment_intent.payment_failed": self._handle_payment_failed,
    "payment_intent.canceled": self._handle_payment_canceled,
    "payment_intent.processing": self._handle_payment_processing,
}
```

**Status:** ✅ PERFECT - Clean handler routing

### 4. ✅ Quick Response
**Stripe Requirement:** Respond quickly (within 5 seconds), process async if needed

**Your Implementation:**
```python
return {"received": True, "result": result}
```

**Status:** ✅ GOOD - You respond immediately after processing

### 5. ✅ Error Handling
**Stripe Requirement:** Return 200 for successfully received webhooks, even if processing fails

**Your Implementation:**
```python
except Exception as e:
    logger.error(f"Webhook processing error: {e}")
    # Still return 200 to prevent Stripe retries for non-retryable errors
    return {"received": True, "error": str(e)}
```

**Status:** ✅ EXCELLENT - You return 200 for non-verification errors

---

## ⚠️ Potential Issues

### 1. ⚠️ Missing Event ID Tracking
**Stripe Recommendation:** Store event IDs to guarantee idempotency across retries

**Current Implementation:**
```python
payment.payment_metadata["stripe_event_id"] = event_id  # Stored but not checked
```

**Issue:** You store the event_id but don't check if you've already processed this specific event. If Stripe retries the same event, you only check payment status, not the event ID.

**Recommendation:**
```python
# Check if this specific event was already processed
if payment.payment_metadata and payment.payment_metadata.get("stripe_event_id") == event_id:
    logger.info(f"Event {event_id} already processed (idempotent)")
    return {"status": "already_processed", "event_id": event_id}
```

### 2. ⚠️ Timestamp Validation Missing
**Stripe Recommendation:** Reject events older than 5 minutes to prevent replay attacks

**Current Implementation:** Not implemented

**Recommendation:** Add timestamp validation:
```python
def verify_webhook_signature(self, payload: bytes, sig_header: str) -> dict:
    try:
        event = self.stripe.Webhook.construct_event(
            payload,
            sig_header,
            self.config.webhook_secret,
            tolerance=300  # 5 minutes
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise ValueError("Invalid webhook signature")
```

### 3. ⚠️ Webhook Secret Validation
**Issue:** If `STRIPE_WEBHOOK_SECRET` is empty, signature verification will fail silently

**Current Implementation:**
```python
self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # Empty string default
```

**Recommendation:** Validate on startup:
```python
def __init__(self):
    self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not self.webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is required")
```

---

## 🔍 Why Webhooks Might Not Be Working

Based on the implementation review, here are the most likely issues:

### Issue 1: Webhook Secret Not Set or Incorrect
**Probability:** 🔴 HIGH

**Check:**
```bash
# On VPS
docker exec coupon-api-container printenv STRIPE_WEBHOOK_SECRET
```

**Should output:** `whsec_...` (starts with whsec_)

**If empty or wrong:** This is your problem!

**Fix:**
1. Get signing secret from Stripe Dashboard → Webhooks → Click your endpoint → Reveal signing secret
2. Update GitHub Secret: `STRIPE_WEBHOOK_SECRET`
3. Redeploy

### Issue 2: Wrong Stripe Mode (Test vs Live)
**Probability:** 🟡 MEDIUM

**Check:**
```bash
# On VPS
docker exec coupon-api-container printenv STRIPE_SECRET_KEY
```

**Should output:**
- Test mode: `sk_test_...`
- Live mode: `sk_live_...`

**Make sure:** Webhook in Stripe Dashboard is in the same mode

### Issue 3: Webhook Not Enabled in Stripe
**Probability:** 🟡 MEDIUM

**Check:** Stripe Dashboard → Webhooks → Status should be "Enabled"

### Issue 4: Events Not Selected
**Probability:** 🟢 LOW

**Check:** Stripe Dashboard → Webhooks → Events to send should include:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.canceled`
- `payment_intent.processing`

---

## 🛠️ Recommended Improvements

### 1. Add Event ID Deduplication

```python
def _handle_payment_succeeded(self, payment_intent: dict, event_id: str) -> dict:
    pi_id = payment_intent.get("id")
    
    payment = self._get_payment_by_intent(pi_id)
    if not payment:
        logger.warning(f"Payment not found for PaymentIntent: {pi_id}")
        return {"status": "not_found", "payment_intent_id": pi_id}
    
    # NEW: Check if this specific event was already processed
    if payment.payment_metadata and payment.payment_metadata.get("stripe_event_id") == event_id:
        logger.info(f"Event {event_id} already processed for payment {payment.id}")
        return {"status": "already_processed", "event_id": event_id}
    
    # Existing idempotency check
    if payment.status == PaymentStatus.SUCCEEDED.value:
        logger.info(f"Payment {payment.id} already marked as succeeded (idempotent)")
        return {"status": "already_processed", "payment_id": str(payment.id)}
    
    # ... rest of the code
```

### 2. Add Timestamp Validation

```python
def verify_webhook_signature(self, payload: bytes, sig_header: str) -> dict:
    try:
        event = self.stripe.Webhook.construct_event(
            payload,
            sig_header,
            self.config.webhook_secret,
            tolerance=300  # Reject events older than 5 minutes
        )
        return event
    except self.stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise ValueError("Invalid webhook signature")
    except Exception as e:
        logger.error(f"Webhook construction failed: {e}")
        raise ValueError(f"Webhook error: {e}")
```

### 3. Add Startup Validation

```python
# In app/main.py or app/config.py
@app.on_event("startup")
async def validate_stripe_config():
    config = get_stripe_config()
    if not config.webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not set!")
        # Don't raise in production, just log
    if not config.secret_key:
        logger.error("STRIPE_SECRET_KEY is not set!")
```

---

## 📊 Implementation Score

| Requirement | Status | Score |
|-------------|--------|-------|
| Signature Verification | ✅ Implemented | 10/10 |
| Raw Body Usage | ✅ Correct | 10/10 |
| Event Type Routing | ✅ Clean | 10/10 |
| Quick Response | ✅ Good | 10/10 |
| Error Handling | ✅ Excellent | 10/10 |
| Idempotency (Status) | ✅ Good | 8/10 |
| Idempotency (Event ID) | ⚠️ Partial | 5/10 |
| Timestamp Validation | ❌ Missing | 0/10 |
| Config Validation | ⚠️ Weak | 3/10 |

**Overall Score:** 76/90 (84%) - **GOOD**

---

## 🎯 Next Steps

1. **Immediate:** Check if `STRIPE_WEBHOOK_SECRET` is set correctly
   ```bash
   ssh root@your-vps
   bash check_stripe_webhook_config.sh
   ```

2. **Test:** Send test webhook from Stripe Dashboard
   - Watch logs: `docker logs -f coupon-api-container`
   - Should see: "Processing webhook event: payment_intent.succeeded"

3. **Improve:** Add event ID deduplication (optional but recommended)

4. **Monitor:** Check Stripe Dashboard → Webhooks → Recent deliveries

---

## Summary

Your implementation is **solid and follows most Stripe best practices**. The core functionality (signature verification, idempotency, error handling) is correct.

If webhooks aren't working, it's almost certainly a **configuration issue** (webhook secret mismatch or not set), not an implementation issue.

Run the diagnostic script to identify the exact problem!
