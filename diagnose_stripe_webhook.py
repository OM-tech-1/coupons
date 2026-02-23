#!/usr/bin/env python3
"""
Diagnose Stripe Webhook Issues

Run this on your server to check:
1. Environment variables are loaded
2. Webhook secret is correct
3. Recent webhook attempts in logs
4. Payment status in database

Usage:
  python3 diagnose_stripe_webhook.py
"""
import os
import sys

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("STRIPE WEBHOOK DIAGNOSTIC")
print("=" * 80)
print()

# 1. Check Environment
env = os.getenv("ENVIRONMENT", "NOT SET")
print(f"1. ENVIRONMENT: {env}")
print()

# 2. Check which Stripe keys should be used
print("2. STRIPE CONFIGURATION:")
print("-" * 80)

if env.lower() == "production":
    print("   Environment is PRODUCTION - should use keys WITHOUT _TEST suffix")
    print()
    sk = os.getenv("STRIPE_SECRET_KEY")
    pk = os.getenv("STRIPE_PUBLISHABLE_KEY")
    wh = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    print(f"   STRIPE_SECRET_KEY: {'✓ SET' if sk else '✗ MISSING'}")
    if sk:
        if sk.startswith("sk_live_"):
            print(f"     → LIVE key (sk_live_...{sk[-4:]})")
        elif sk.startswith("sk_test_"):
            print(f"     → ⚠ WARNING: TEST key in production!")
        else:
            print(f"     → ⚠ Unknown format")
    
    print(f"   STRIPE_PUBLISHABLE_KEY: {'✓ SET' if pk else '✗ MISSING'}")
    print(f"   STRIPE_WEBHOOK_SECRET: {'✓ SET' if wh else '✗ MISSING'}")
    if wh:
        if wh.startswith("whsec_"):
            print(f"     → Valid format (whsec_...{wh[-4:]})")
        else:
            print(f"     → ⚠ Invalid format (should start with whsec_)")
else:
    print(f"   Environment is '{env}' - should use keys WITH _TEST suffix")
    print()
    sk = os.getenv("STRIPE_SECRET_KEY_TEST")
    pk = os.getenv("STRIPE_PUBLISHABLE_KEY_TEST")
    wh = os.getenv("STRIPE_WEBHOOK_SECRET_TEST")
    
    print(f"   STRIPE_SECRET_KEY_TEST: {'✓ SET' if sk else '✗ MISSING'}")
    if sk:
        if sk.startswith("sk_test_"):
            print(f"     → TEST key (sk_test_...{sk[-4:]})")
        elif sk.startswith("sk_live_"):
            print(f"     → ⚠ WARNING: LIVE key in test environment!")
        else:
            print(f"     → ⚠ Unknown format")
    
    print(f"   STRIPE_PUBLISHABLE_KEY_TEST: {'✓ SET' if pk else '✗ MISSING'}")
    print(f"   STRIPE_WEBHOOK_SECRET_TEST: {'✓ SET' if wh else '✗ MISSING'}")
    if wh:
        if wh.startswith("whsec_"):
            print(f"     → Valid format (whsec_...{wh[-4:]})")
        else:
            print(f"     → ⚠ Invalid format (should start with whsec_)")

print()

# 3. Check database connection
print("3. DATABASE CHECK:")
print("-" * 80)

try:
    from app.database import SessionLocal
    from app.models.payment import Payment
    from app.models.order import Order
    from sqlalchemy import desc
    
    db = SessionLocal()
    
    # Check recent payments
    recent_payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(5).all()
    
    print(f"   Found {len(recent_payments)} recent payments")
    print()
    
    if recent_payments:
        print("   Recent Payments:")
        for p in recent_payments:
            order = db.query(Order).filter(Order.id == p.order_id).first()
            print(f"     • Payment ID: {p.id}")
            print(f"       Status: {p.status}")
            print(f"       Amount: {p.amount} {p.currency}")
            print(f"       Stripe PI: {p.stripe_payment_intent_id}")
            if order:
                print(f"       Order Status: {order.status}")
            print(f"       Created: {p.created_at}")
            print()
    
    # Check pending payments
    pending = db.query(Payment).filter(Payment.status == "pending").count()
    print(f"   Pending payments: {pending}")
    
    # Check succeeded payments
    succeeded = db.query(Payment).filter(Payment.status == "succeeded").count()
    print(f"   Succeeded payments: {succeeded}")
    
    db.close()
    
except Exception as e:
    print(f"   ✗ Database error: {e}")

print()

# 4. Test webhook secret loading
print("4. WEBHOOK SECRET LOADING TEST:")
print("-" * 80)

try:
    from app.utils.stripe_client import get_stripe_config
    
    config = get_stripe_config()
    
    print(f"   Environment detected: {config.environment}")
    print(f"   Secret key loaded: {'✓ YES' if config.secret_key else '✗ NO'}")
    print(f"   Webhook secret loaded: {'✓ YES' if config.webhook_secret else '✗ NO'}")
    
    if config.webhook_secret:
        if config.webhook_secret.startswith("whsec_"):
            print(f"   Webhook secret format: ✓ Valid (whsec_...{config.webhook_secret[-4:]})")
        else:
            print(f"   Webhook secret format: ✗ Invalid (doesn't start with whsec_)")
    
    print()
    
except Exception as e:
    print(f"   ✗ Error loading config: {e}")
    print()

# 5. Instructions
print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print()

if not wh:
    print("❌ WEBHOOK SECRET IS MISSING!")
    print()
    print("   1. Check your .env file or environment variables")
    if env.lower() == "production":
        print("   2. Ensure STRIPE_WEBHOOK_SECRET is set")
    else:
        print("   2. Ensure STRIPE_WEBHOOK_SECRET_TEST is set")
    print("   3. Get the secret from Stripe Dashboard:")
    print("      → Developers → Webhooks → Select your webhook → Signing secret")
    print()
else:
    print("✓ Webhook secret is loaded")
    print()
    print("If payments are still pending:")
    print()
    print("   1. Check Stripe Dashboard → Developers → Webhooks")
    print("   2. Verify webhook endpoint: https://api.vouchergalaxy.com/webhooks/stripe")
    print("   3. Check webhook events are configured:")
    print("      • payment_intent.succeeded")
    print("      • payment_intent.payment_failed")
    print("      • payment_intent.canceled")
    print("   4. Click on recent webhook attempts to see errors")
    print("   5. Verify the webhook secret matches what's in your environment")
    print()
    print("   To test webhook manually:")
    print("   → Stripe Dashboard → Webhooks → Your webhook → Send test webhook")
    print()

print("=" * 80)
