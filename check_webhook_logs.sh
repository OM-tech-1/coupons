#!/bin/bash
# Check webhook logs in production

echo "Checking webhook logs..."
echo "========================"
echo ""
echo "Looking for webhook-related logs in the last 100 lines:"
echo ""

# Check if running in Docker
if docker ps | grep -q coupon-api-container; then
    docker logs coupon-api-container --tail 100 | grep -i "webhook\|stripe\|payment_intent"
else
    echo "Container not running. Start it first with: make deploy"
fi
