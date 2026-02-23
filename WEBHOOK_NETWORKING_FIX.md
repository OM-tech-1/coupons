# Stripe Webhook Networking Issue - Fix Guide

## Problem Identified

Your Docker container is bound to `127.0.0.1:8000`, which means it's only accessible from localhost on the server. Stripe webhooks coming from the internet cannot reach it.

**In your CI/CD pipeline (`.github/workflows/ci-cd.yml` line 73):**
```yaml
-p 127.0.0.1:8000:8000  # ❌ Only accessible from localhost
```

## Why This Happens

- `127.0.0.1:8000:8000` = Only the server itself can access the app
- Stripe webhooks come from Stripe's servers on the internet
- They cannot reach `127.0.0.1` on your server

## Solution: Setup Nginx Reverse Proxy (Recommended)

This is the production-ready approach that also gives you SSL/HTTPS.

### Step 1: Run Diagnostic (Optional)

On your VPS server:
```bash
bash diagnose_webhook_networking.sh
```

### Step 2: Setup Nginx

On your VPS server (as root):
```bash
sudo bash setup_nginx_webhook.sh
```

This will:
- Install nginx
- Configure it to proxy requests to your container
- Enable the configuration

### Step 3: Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Step 4: Update Stripe Webhook URL

In your Stripe Dashboard:
1. Go to Developers → Webhooks
2. Update webhook URL to: `https://your-domain.com/webhooks/stripe`
3. Make sure these events are selected:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
   - `payment_intent.processing`

### Step 5: Test

```bash
# Test from your local machine (not the server)
curl -X POST https://your-domain.com/webhooks/stripe

# Should return 400 with "Missing Stripe-Signature header"
# This means the endpoint is reachable!
```

## Alternative: Expose Container Directly (Not Recommended)

If you don't want to use nginx, you can expose the container directly, but you'll still need SSL.

### Update CI/CD Pipeline

Change line 73 in `.github/workflows/ci-cd.yml`:
```yaml
-p 0.0.0.0:8000:8000  # Exposes to all interfaces
```

But this approach:
- ❌ Exposes your app directly to the internet
- ❌ No SSL termination
- ❌ No rate limiting or security features
- ❌ Stripe requires HTTPS for webhooks

## For Local Development: Stripe CLI

If you're testing locally:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe  # macOS
# or download from https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks to local container
stripe listen --forward-to http://localhost:8000/webhooks/stripe

# Use the webhook signing secret from the CLI output
# Update STRIPE_WEBHOOK_SECRET in your .env
```

## Verification Checklist

- [ ] Nginx is installed and running
- [ ] SSL certificate is installed (Let's Encrypt)
- [ ] DNS points to your server
- [ ] Firewall allows ports 80 and 443
- [ ] Stripe webhook URL is updated to HTTPS
- [ ] Test webhook returns 400 (missing signature)
- [ ] Container logs show webhook attempts

## Troubleshooting

### Check if nginx is running
```bash
sudo systemctl status nginx
```

### Check nginx logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check container logs
```bash
docker logs -f coupon-api-container
```

### Test webhook endpoint locally on server
```bash
curl -X POST http://localhost:8000/webhooks/stripe
# Should return 400
```

### Test webhook endpoint from internet
```bash
curl -X POST https://your-domain.com/webhooks/stripe
# Should return 400
```

### Check firewall
```bash
sudo ufw status
# Make sure 80 and 443 are allowed
sudo ufw allow 80
sudo ufw allow 443
```

## Network Flow Diagram

```
Internet (Stripe)
    ↓
    ↓ HTTPS (443)
    ↓
Your Server (Public IP)
    ↓
Nginx (Port 80/443)
    ↓
    ↓ HTTP
    ↓
Docker Container (127.0.0.1:8000)
    ↓
FastAPI App
```

## Quick Commands Reference

```bash
# On VPS Server:

# 1. Check container status
docker ps | grep coupon-api

# 2. Check nginx status
sudo systemctl status nginx

# 3. Test locally
curl http://localhost:8000/health

# 4. Test externally (from your local machine)
curl https://your-domain.com/health

# 5. Watch logs
docker logs -f coupon-api-container
sudo tail -f /var/log/nginx/access.log

# 6. Restart services
sudo systemctl restart nginx
docker restart coupon-api-container
```

## Summary

The issue is networking, not your code. Your container is hidden behind localhost. Set up nginx as a reverse proxy with SSL, and Stripe webhooks will work perfectly.
