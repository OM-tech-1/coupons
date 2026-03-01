#!/bin/bash

# Docker Quick Start Script for Coupon App
# This script sets up the local development environment with Docker

set -e

echo "🚀 Starting Coupon App Docker Environment"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.docker .env
    echo "⚠️  Please edit .env with your configuration (JWT secret, Stripe keys, etc.)"
    echo "   Then run this script again."
    exit 0
fi

echo "✅ .env file found"

# Start Docker services
echo ""
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
if docker exec coupon_postgres pg_isready -U coupon_user -d coupon_db > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready. Check logs: docker-compose logs postgres"
    exit 1
fi

# Check Redis
if docker exec coupon_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready. Check logs: docker-compose logs redis"
    exit 1
fi

echo ""
echo "=========================================="
echo "✨ Docker services are running!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis:      localhost:6379"
echo ""
echo "🔗 Connection Strings:"
echo "   DATABASE_URL: postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db"
echo "   REDIS_URL:    redis://localhost:6379/0"
echo ""
echo "📝 Next Steps:"
echo "   1. Activate virtual environment:"
echo "      source .venv/bin/activate"
echo ""
echo "   2. Run database migrations:"
echo "      python -m alembic upgrade head"
echo ""
echo "   3. (Optional) Seed data:"
echo "      python scripts/seed_regions_countries.py"
echo "      python create_admin.py"
echo ""
echo "   4. Start the application:"
echo "      uvicorn app.main:app --reload"
echo ""
echo "🛠️  Management Tools (optional):"
echo "   docker-compose --profile tools up -d"
echo "   - pgAdmin:        http://localhost:5050"
echo "   - Redis Commander: http://localhost:8081"
echo ""
echo "📖 For more info, see DOCKER_SETUP.md"
echo ""
