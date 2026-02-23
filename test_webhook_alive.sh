#!/bin/bash
# Quick test to check if webhook endpoint is alive

echo "Testing webhook endpoint..."
echo "URL: https://api.vouchergalaxy.com/webhooks/stripe"
echo ""

# Test if endpoint responds
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  https://api.vouchergalaxy.com/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}' \
  --max-time 10)

echo "Response code: $response"
echo ""

case $response in
  000)
    echo "❌ FAILED: Cannot connect to server"
    echo "   - Server might be down"
    echo "   - Check if application is deployed"
    ;;
  404)
    echo "❌ FAILED: Endpoint not found"
    echo "   - Application might not be running"
    echo "   - Check deployment"
    ;;
  400|401)
    echo "✅ SUCCESS: Endpoint is alive!"
    echo "   - Server is responding"
    echo "   - Webhook endpoint exists"
    echo "   - Ready to receive Stripe webhooks"
    ;;
  500)
    echo "⚠️  WARNING: Server error"
    echo "   - Endpoint exists but has a bug"
    echo "   - Check application logs"
    ;;
  *)
    echo "⚠️  Unexpected response: $response"
    ;;
esac

echo ""
echo "Next steps:"
echo "1. Configure webhook in Stripe Dashboard"
echo "2. Use 'Send test webhook' button in Stripe"
echo "3. Check for green checkmark ✅"
