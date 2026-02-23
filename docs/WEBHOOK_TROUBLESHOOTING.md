# Stripe Webhook Troubleshooting Guide

## Issue: Payments Stuck in Pending Status

If payments remain in "pending" status and never update to "paid", the webhook is not working properly.

## Root Cause

The webhook secret was not being loaded correctly based on the environment. The code was hardcoded to use `STRIPE_WEBHOOK_SECRET` instead of checking the `ENVIRONMENT` variable and using `STRIPE_WEBHOOK_SECRET_TEST` for test environments.

## Fix Applied

Updated `app/utils/stripe_client.py` to:
1. Check the `ENVIRONMENT` variable
2. Use `_TEST` suffixed keys for non-production environments
3. Use non-suffixed keys for production

```python
if environment == "production":
    self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
else:
    self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET_TEST") or os.getenv("STRIPE_WEBHOOK_SECRET", "")
```

## Diagnostic Steps

### 1. Check Environment Variables on Server

Run this script on your server via SSH:

```bash
python3 check_secrets.py
```

This will show:
- Which environment variables are set
- Preview of secret values (first/last chars only)
- Whether webhook secret is in correct format (starts with `whsec_`)

### 2. Run Full Diagnostic

For detailed webhook diagnostics:

```bash
python3 diagnose_stripe_webhook.py
```

This checks:
- Environment configuration
- Stripe key loading
- Recent payments in database
- Webhook secret format

### 3. Check Stripe Dashboard

1. Go to Stripe Dashboard → Developers → Webhooks
2. Find your webhook endpoint: `https://api.vouchergalaxy.com/webhooks/stripe`
3. Click on it to see recent webhook attempts
4. Look for errors in the "Recent deliveries" section

Common errors:
- **401 Unauthorized**: Webhook secret mismatch
- **400 Bad Request**: Signature verification failed
- **500 Server Error**: Application error (check logs)

### 4. Verify Webhook Configuration

In Stripe Dashboard, ensure these events are selected:
- `payment_intent.succeeded` ✓
- `payment_intent.payment_failed` ✓
- `payment_intent.canceled` ✓
- `payment_intent.processing` ✓

### 5. Test Webhook Manually

In Stripe Dashboard:
1. Go to your webhook
2. Click "Send test webhook"
3. Select `payment_intent.succeeded`
4. Check if it succeeds

## Environment Variables Required

### Test Environment (default)
```bash
ENVIRONMENT=test  # or not set
STRIPE_SECRET_KEY_TEST=sk_test_...
STRIPE_PUBLISHABLE_KEY_TEST=pk_test_...
STRIPE_WEBHOOK_SECRET_TEST=whsec_...
```

### Production Environment
```bash
ENVIRONMENT=production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Getting Webhook Secret from Stripe

1. Go to Stripe Dashboard
2. Navigate to Developers → Webhooks
3. Click on your webhook endpoint
4. Click "Reveal" next to "Signing secret"
5. Copy the secret (starts with `whsec_`)
6. Add to your environment variables or GitHub Secrets

## GitHub Secrets Configuration

For CI/CD deployment, add to GitHub Secrets:
- `STRIPE_WEBHOOK_SECRET_TEST` for test environment
- `STRIPE_WEBHOOK_SECRET` for production

The deployment workflow will inject these based on the `ENVIRONMENT` variable.

## Verification After Fix

1. Deploy the updated code
2. Make a test payment
3. Check payment status updates to "paid"
4. Verify coupons appear in user's wallet
5. Check Stripe Dashboard shows successful webhook delivery

## Common Issues

### Issue: Webhook secret not loaded
**Solution**: Ensure environment variable is set correctly with `_TEST` suffix for test environments

### Issue: Signature verification fails
**Solution**: Webhook secret in environment doesn't match the one in Stripe Dashboard

### Issue: Webhook endpoint not reachable
**Solution**: Check firewall rules, ensure endpoint is publicly accessible

### Issue: Payments succeed but coupons not added
**Solution**: Check webhook is configured and receiving `payment_intent.succeeded` events

## Related Files
- `app/utils/stripe_client.py` - Stripe configuration loading
- `app/api/stripe/webhooks.py` - Webhook endpoint
- `app/services/stripe/webhook_service.py` - Webhook processing logic
- `check_secrets.py` - Environment variable checker
- `diagnose_stripe_webhook.py` - Full diagnostic script
