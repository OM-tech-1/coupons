#!/bin/bash

# Deployment Script for Coupon API
# Usage: ./deploy.sh

# Stop on error
set -e

echo "🚀 Starting Deployment..."

# 1. Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# 2. Verify REDIS_URL is configured
if ! grep -q "REDIS_URL" .env; then
    echo "⚠️  REDIS_URL not found in .env. Please add it before deploying."
    echo "   Example: REDIS_URL=redis://:yourpassword@host:6379/0"
    exit 1
fi

# 3. Rebuild Docker container
echo "🐳 Rebuilding Docker container..."
docker build -t coupon-api .

# 4. Run database migrations BEFORE starting the app
echo "🗄️  Running Alembic migrations..."
# Run in a throwaway container so the app never starts with a stale schema.
# If any migration fails, the script exits here (set -e) and the app is NOT restarted.
docker run --rm --env-file .env coupon-api alembic upgrade head
echo "✅ Migrations applied successfully!"

# 5. Restart Container
echo "🔄 Restarting container..."
docker stop coupon-api-container 2>/dev/null || true
docker rm coupon-api-container 2>/dev/null || true
# Stop old container name if exists
docker stop coupons-app 2>/dev/null || true
docker rm coupons-app 2>/dev/null || true

docker run -d \
  --name coupon-api-container \
  --restart unless-stopped \
  --network host \
  --env-file .env \
  coupon-api

# 6. Verify Health
echo "🏥 Verifying deployment..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ Deployment Successful! API is healthy."
else
    echo "⚠️ Health check failed with status $HTTP_STATUS. Please check logs: docker logs coupon-api-container"
fi
