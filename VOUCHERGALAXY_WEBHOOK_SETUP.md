# VoucherGalaxy Stripe Webhook Setup Guide

## Problem Summary

Your Docker container is bound to `127.0.0.1:8000`, making it inaccessible from the internet. Stripe webhooks cannot reach it.

**Current Setup:**
- Container: `127.0.0.1:8000` (localhost only)
- Domain: `api.vouchergalaxy.com`
- Webhook URL needed: `https://api.vouchergalaxy.com/webhooks/stripe`

## Solution: Nginx Reverse Proxy

Set up Nginx to act as a public-facing proxy that forwards requests to your container.

---

## Step-by-Step Setup

### 1. Upload Scripts to VPS

From your local machine:

```bash
# Upload the deployment script
scp deploy_nginx_vouchergalaxy.sh root@your-vps-ip:/root/
scp verify_webhook_setup.sh root@your-vps-ip:/root/
```

### 2. SSH into Your VPS

```bash
ssh root@your-vps-ip
```

### 3. Run the Nginx Setup Script

```bash
cd /root
chmod +x deploy_nginx_vouchergalaxy.sh
sudo bash deploy_nginx_vouchergalaxy.sh
```

This will:
- ✅ Install Nginx
- ✅ Configure reverse proxy for api.vouchergalaxy.com
- ✅ Enable the site
- ✅ Configure firewall
- ✅ Test basic connectivity

### 4. Verify DNS Configuration

Make sure `api.vouchergalaxy.com` points to your VPS IP:

```bash
dig api.vouchergalaxy.com
```

If not configured, update your DNS records:
- Type: A
- Name: api
- Value: [Your VPS IP]
- TTL: 300

Wait 5-10 minutes for DNS propagation.

### 5. Install SSL Certificate

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d api.vouchergalaxy.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)
```

### 6. Verify Setup

```bash
chmod +x verify_webhook_setup.sh
bash verify_webhook_setup.sh
```

This will check:
- DNS resolution
- Container status
- Nginx configuration
- SSL certificate
- External accessibility

### 7. Test Webhook Endpoint

From your local machine:

```bash
curl -X POST https://api.vouchergalaxy.com/webhooks/stripe
```

Expected response:
```json
{"detail":"Missing Stripe-Signature header"}
```

This is correct! It means the endpoint is reachable.

### 8. Update Stripe Dashboard

1. Go to: https://dashboard.stripe.com/webhooks
2. Click on your webhook endpoint (or create new)
3. Update URL to: `https://api.vouchergalaxy.com/webhooks/stripe`
4. Select events:
   - ✅ `payment_intent.succeeded`
   - ✅ `payment_intent.payment_failed`
   - ✅ `payment_intent.canceled`
   - ✅ `payment_intent.processing`
5. Save

### 9. Test with Stripe

In Stripe Dashboard:
1. Go to your webhook
2. Click "Send test webhook"
3. Select `payment_intent.succeeded`
4. Click "Send test webhook"

Check logs:
```bash
# Container logs
docker logs -f coupon-api-container

# Nginx logs
sudo tail -f /var/log/nginx/vouchergalaxy-api-access.log
```

You should see the webhook request!

---

## Verification Checklist

- [ ] Nginx installed and running
- [ ] DNS points api.vouchergalaxy.com to VPS
- [ ] SSL certificate installed
- [ ] Webhook endpoint returns 400 (missing signature)
- [ ] Stripe webhook URL updated
- [ ] Test webhook sent from Stripe
- [ ] Container logs show webhook received

---

## Troubleshooting

### DNS Not Resolving

```bash
# Check DNS
dig api.vouchergalaxy.com

# Should show your VPS IP
# If not, update DNS and wait 5-10 minutes
```

### Nginx Not Starting

```bash
# Check nginx status
sudo systemctl status nginx

# Check configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log
```

### Container Not Responding

```bash
# Check container status
docker ps | grep coupon-api

# Check container logs
docker logs coupon-api-container

# Restart container
docker restart coupon-api-container
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

### Webhook Not Receiving Events

```bash
# Check nginx access logs
sudo tail -f /var/log/nginx/vouchergalaxy-api-access.log

# Check container logs
docker logs -f coupon-api-container | grep webhook

# Test locally
curl -X POST http://localhost:8000/webhooks/stripe

# Test via nginx
curl -X POST http://localhost/webhooks/stripe

# Test externally
curl -X POST https://api.vouchergalaxy.com/webhooks/stripe
```

### Firewall Blocking

```bash
# Check firewall
sudo ufw status

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Reload firewall
sudo ufw reload
```

---

## Network Flow

```
Stripe Servers
    ↓
    ↓ HTTPS (443)
    ↓
Internet
    ↓
Your VPS (Public IP)
    ↓
Nginx (Port 80/443)
    ↓ SSL Termination
    ↓ HTTP
    ↓
Docker Container (127.0.0.1:8000)
    ↓
FastAPI App (/webhooks/stripe)
    ↓
Webhook Processing
```

---

## Useful Commands

```bash
# Check everything
bash verify_webhook_setup.sh

# Restart services
sudo systemctl restart nginx
docker restart coupon-api-container

# View logs
sudo tail -f /var/log/nginx/vouchergalaxy-api-access.log
docker logs -f coupon-api-container

# Test endpoints
curl https://api.vouchergalaxy.com/health
curl -X POST https://api.vouchergalaxy.com/webhooks/stripe

# Check SSL
sudo certbot certificates
openssl s_client -connect api.vouchergalaxy.com:443 -servername api.vouchergalaxy.com

# Nginx commands
sudo nginx -t                    # Test config
sudo systemctl status nginx      # Check status
sudo systemctl reload nginx      # Reload config
sudo systemctl restart nginx     # Restart service
```

---

## After Setup

Once everything is working:

1. ✅ Webhooks will be received in real-time
2. ✅ Payments will be processed automatically
3. ✅ User coupons will be added to wallets
4. ✅ Order statuses will update correctly

Monitor your logs for the first few transactions to ensure everything works smoothly!

---

## Support

If you encounter issues:

1. Run `bash verify_webhook_setup.sh` and share output
2. Check container logs: `docker logs coupon-api-container`
3. Check nginx logs: `sudo tail -100 /var/log/nginx/vouchergalaxy-api-error.log`
4. Test webhook manually from Stripe Dashboard
