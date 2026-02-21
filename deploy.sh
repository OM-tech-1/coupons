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

# 4. Restart Container
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

# 5. Run Database Indexes
echo "🗄️ Applying database indexes..."
# Assuming postgres container or external DB. If external (Supabase), we need psql installed.
# Using the app container to run psql might be tricky if psql isn't installed in the slim image.
# We'll try to run it using the DATABASE_URL from .env if psql is available on host.

# Run Python script inside container to apply indexes
# This avoids needing psql on the host machine
echo "🚀 Running add_indexes.py inside container..."
docker exec coupon-api-container python scripts/add_indexes.py || echo "⚠️ Index application failed (check logs)"
echo "✅ Index check complete!"

# 6. Verify Health
echo "🏥 Verifying deployment..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ Deployment Successful! API is healthy."
else
    echo "⚠️ Health check failed with status $HTTP_STATUS. Please check logs: docker logs coupon-api-container"
fi
