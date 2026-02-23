# Webhook Issue Diagnosis Checklist

## Step 1: Check Stripe Dashboard

Go to: https://dashboard.stripe.com/test/webhooks

### Questions to Answer:

1. **Is the webhook endpoint configured?**
   - [ ] Yes, I see my endpoint: `https://api.vouchergalaxy.com/webhooks/stripe`
   - [ ] No, I need to add it

2. **What events are selected?**
   - [ ] payment_intent.succeeded
   - [ ] payment_intent.payment_failed
   - [ ] payment_intent.canceled
   - [ ] payment_intent.processing

3. **Are there recent deliveries?**
   - [ ] Yes, with GREEN checkmarks (✅ working)
   - [ ] Yes, with RED X's (❌ failing - click to see error)
   - [ ] No deliveries at all (webhook not being triggered)

4. **If RED X's, what's the error?**
   - [ ] 401 Unauthorized → Wrong webhook secret
   - [ ] 404 Not Found → Wrong URL or app not deployed
   - [ ] 500 Server Error → Bug in code
   - [ ] Timeout → Server too slow

---

## Step 2: Check Environment Variables

### In Production (GitHub Secrets):

1. **Is STRIPE_WEBHOOK_SECRET_TEST set?**
   - [ ] Yes
   - [ ] No - ADD IT NOW

2. **Is ENVIRONMENT set correctly?**
   - [ ] Set to "test" (or not set)
   - [ ] Set to "production"

3. **Did you redeploy after adding secrets?**
   - [ ] Yes
   - [ ] No - REDEPLOY NOW: `git push`

---

## Step 3: Check Application Status

### Is your application running?

```bash
# Check container status
docker ps | grep coupon-api-container

# Check logs
make logs
```

1. **Is container running?**
   - [ ] Yes
   - [ ] No - Start it: `make deploy`

2. **Any errors in logs?**
   - [ ] No errors
   - [ ] Yes - what errors? _______________

---

## Step 4: Test Payment Flow

### Make a test payment:

1. **Create a test order**
2. **Use Stripe test card:** `4242 4242 4242 4242`
3. **Complete payment**
4. **Check:**
   - [ ] Order status changed to "paid"
   - [ ] Coupons appeared in wallet
   - [ ] Webhook delivery in Stripe Dashboard shows green checkmark

---

## Step 5: Check Database

### Verify payment record exists:

```sql
SELECT id, order_id, status, stripe_payment_intent_id 
FROM payments 
ORDER BY created_at DESC 
LIMIT 5;
```

1. **Does payment record exist?**
   - [ ] Yes
   - [ ] No - payment not created

2. **What's the payment status?**
   - [ ] pending
   - [ ] succeeded
   - [ ] failed

3. **Does order exist?**
   - [ ] Yes
   - [ ] No

4. **What's the order status?**
   - [ ] pending_payment
   - [ ] paid
   - [ ] failed

---

## Common Issues & Solutions

### Issue 1: Webhook Secret Not Configured
**Symptoms:** 401 errors in Stripe Dashboard

**Solution:**
1. Get secret from Stripe Dashboard
2. Add to GitHub Secrets: `STRIPE_WEBHOOK_SECRET_TEST`
3. Redeploy: `git push`

### Issue 2: Wrong Webhook URL
**Symptoms:** 404 errors in Stripe Dashboard

**Solution:**
1. Check URL in Stripe Dashboard
2. Should be: `https://api.vouchergalaxy.com/webhooks/stripe`
3. Update if wrong

### Issue 3: Application Not Running
**Symptoms:** Connection errors, timeouts

**Solution:**
```bash
make deploy
make logs
```

### Issue 4: Payment Intent Not Found
**Symptoms:** Webhook succeeds but status not updated

**Solution:**
- Check if payment record exists in database
- Check if `stripe_payment_intent_id` matches
- Check application logs for errors

### Issue 5: Webhook Not Being Sent
**Symptoms:** No deliveries in Stripe Dashboard

**Solution:**
- Make sure you're making TEST payments
- Make sure webhook is in TEST mode
- Check if events are selected correctly

---

## Quick Test Commands

```bash
# Check logs
make logs | grep -i webhook

# Check container status
docker ps | grep coupon-api

# Test webhook endpoint
python test_webhook_endpoint.py

# Check Stripe Dashboard
open https://dashboard.stripe.com/test/webhooks
```

---

## Still Not Working?

If you've checked everything above and it's still not working:

1. **Share the error from Stripe Dashboard**
   - Go to webhook → Recent deliveries
   - Click on failed delivery
   - Copy the error message

2. **Share application logs**
   ```bash
   make logs | tail -100
   ```

3. **Check webhook handler code**
   - File: `app/api/stripe/webhooks.py`
   - File: `app/services/stripe/webhook_service.py`
