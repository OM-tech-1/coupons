#!/bin/bash

# Deployment Script for Coupon API
# Usage: ./deploy.sh

# Stop on error
set -e

echo "🚀 Starting Deployment..."

# 1. Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# 2. Update .env with Redis URL if not exists
if ! grep -q "REDIS_URL" .env; then
    echo "⚙️ Configuring Redis in .env..."
    # Note: %40 is the URL-encoded '@' symbol
    echo "REDIS_URL=redis://:backend%402026@193.203.160.61:6379/0" >> .env
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

if command -v psql &> /dev/null; then
    # Extract DB URL from .env
    DB_URL=$(grep DATABASE_URL .env | cut -d '=' -f2)
    psql "$DB_URL" -f migrations/add_indexes.sql
    echo "✅ Indexes applied!"
else
    echo "⚠️ 'psql' not found on host. Skipping index application."
    echo "👉 Please run 'migrations/add_indexes.sql' manually on your database."
fi

# 6. Verify Health
echo "🏥 Verifying deployment..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ Deployment Successful! API is healthy."
else
    echo "⚠️ Health check failed with status $HTTP_STATUS. Please check logs: docker logs coupon-api-container"
fi
