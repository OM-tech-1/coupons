# Makefile for Coupon API

.PHONY: help setup docker-setup docker-up docker-down docker-restart docker-logs docker-clean docker-db docker-redis docker-tools venv install migrate-up docker-migrate seed-db create-admin-local run dev test test-coverage clean deploy redeploy logs logs-webhook logs-errors shell stop restart status clean-db create-admin seed-data migrate setup-load-test load-test load-test-headless benchmark benchmark-simple

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║          Coupon API - Development Commands                ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start (For Interns/New Developers):$(NC)"
	@echo "  $(YELLOW)make setup$(NC)              - Complete setup (venv + docker + deps + db)"
	@echo "  $(YELLOW)make dev$(NC)                - Start development server"
	@echo ""
	@echo "$(GREEN)🐳 Docker Commands (Local Development):$(NC)"
	@echo "  $(YELLOW)make docker-setup$(NC)       - Initial Docker setup (one-time)"
	@echo "  $(YELLOW)make docker-up$(NC)          - Start PostgreSQL + Redis"
	@echo "  $(YELLOW)make docker-migrate$(NC)     - Run database migrations inside Docker"
	@echo "  $(YELLOW)make docker-down$(NC)        - Stop all Docker services"
	@echo "  $(YELLOW)make docker-restart$(NC)     - Restart Docker services"
	@echo "  $(YELLOW)make docker-logs$(NC)        - View Docker logs"
	@echo "  $(YELLOW)make docker-clean$(NC)       - Stop and remove all data (⚠️  destructive)"
	@echo "  $(YELLOW)make docker-db$(NC)          - Connect to PostgreSQL CLI"
	@echo "  $(YELLOW)make docker-redis$(NC)       - Connect to Redis CLI"
	@echo "  $(YELLOW)make docker-tools$(NC)       - Start pgAdmin + Redis Commander"
	@echo ""
	@echo "$(GREEN)🔧 Development Commands:$(NC)"
	@echo "  $(YELLOW)make venv$(NC)               - Create Python virtual environment"
	@echo "  $(YELLOW)make install$(NC)            - Install Python dependencies"
	@echo "  $(YELLOW)make migrate-up$(NC)         - Run database migrations"
	@echo "  $(YELLOW)make seed-db$(NC)            - Seed database with initial data"
	@echo "  $(YELLOW)make create-admin-local$(NC) - Create admin user (local)"
	@echo "  $(YELLOW)make run$(NC)                - Run app locally (port 8000)"
	@echo "  $(YELLOW)make dev$(NC)                - Run app with auto-reload"
	@echo "  $(YELLOW)make test$(NC)               - Run all tests"
	@echo "  $(YELLOW)make test-coverage$(NC)      - Run tests with coverage report"
	@echo "  $(YELLOW)make clean$(NC)              - Clean up cache and temp files"
	@echo ""
	@echo "$(GREEN)📦 Production Commands (Server):$(NC)"
	@echo "  $(YELLOW)make deploy$(NC)             - Deploy to production server"
	@echo "  $(YELLOW)make logs$(NC)               - View production logs"
	@echo "  $(YELLOW)make logs-webhook$(NC)       - View webhook logs only"
	@echo "  $(YELLOW)make logs-errors$(NC)        - View error logs only"
	@echo "  $(YELLOW)make shell$(NC)              - Open shell in production container"
	@echo "  $(YELLOW)make status$(NC)             - Check production container status"
	@echo "  $(YELLOW)make restart$(NC)            - Restart production container"
	@echo ""
	@echo "$(GREEN)🧪 Load Testing:$(NC)"
	@echo "  $(YELLOW)make setup-load-test$(NC)    - Install load testing tools"
	@echo "  $(YELLOW)make benchmark-simple$(NC)   - Simple benchmark (curl only)"
	@echo "  $(YELLOW)make load-test$(NC)          - Interactive load test (Web UI)"
	@echo "  $(YELLOW)make benchmark$(NC)          - Quick benchmark (100 users)"
	@echo ""
	@echo "$(BLUE)📖 Documentation:$(NC)"
	@echo "  See DOCKER_SETUP.md for detailed Docker guide"
	@echo "  See README.md for project documentation"
	@echo ""

# ============== Quick Setup Commands ==============

setup: venv install docker-setup docker-up docker-migrate seed-db create-admin-local
	@echo ""
	@echo "$(GREEN)✨ Setup complete! You're ready to develop.$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Activate virtual environment: $(BLUE)source .venv/bin/activate$(NC)"
	@echo "  2. Start development server:     $(BLUE)make dev$(NC)"
	@echo "  3. Open browser:                 $(BLUE)http://localhost:8000$(NC)"
	@echo "  4. View API docs:                $(BLUE)http://localhost:8000/docs$(NC)"
	@echo ""

# ============== Docker Commands ==============

docker-setup:
	@echo "$(BLUE)🐳 Setting up Docker environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)📝 Creating .env from template...$(NC)"; \
		cp .env.docker .env; \
		echo "$(GREEN)✅ .env created. Please update with your configuration.$(NC)"; \
	else \
		echo "$(GREEN)✅ .env already exists$(NC)"; \
	fi
	@chmod +x docker-start.sh
	@echo "$(GREEN)✅ Docker setup complete$(NC)"

docker-up:
	@echo "$(BLUE)🚀 Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(YELLOW)⏳ Waiting for services to be ready...$(NC)"
	@sleep 5
	@docker-compose ps
	@echo "$(GREEN)✅ Docker services are running$(NC)"
	@echo ""
	@echo "$(BLUE)📊 Service URLs:$(NC)"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis:      localhost:6379"

docker-down:
	@echo "$(BLUE)🛑 Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✅ Docker services stopped$(NC)"

docker-restart:
	@echo "$(BLUE)🔄 Restarting Docker services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✅ Docker services restarted$(NC)"

docker-logs:
	@echo "$(BLUE)📋 Viewing Docker logs (Ctrl+C to exit)...$(NC)"
	@docker-compose logs -f

docker-clean:
	@echo "$(RED)⚠️  WARNING: This will delete all Docker data!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read confirm
	@docker-compose down -v
	@echo "$(GREEN)✅ Docker services and data removed$(NC)"

docker-db:
	@echo "$(BLUE)🗄️  Connecting to PostgreSQL...$(NC)"
	@docker exec -it coupon_postgres psql -U coupon_user -d coupon_db

docker-redis:
	@echo "$(BLUE)📦 Connecting to Redis...$(NC)"
	@docker exec -it coupon_redis redis-cli

docker-tools:
	@echo "$(BLUE)🛠️  Starting management tools...$(NC)"
	@docker-compose --profile tools up -d
	@echo "$(GREEN)✅ Management tools started$(NC)"
	@echo ""
	@echo "$(BLUE)🌐 Access URLs:$(NC)"
	@echo "  pgAdmin:        http://localhost:5050"
	@echo "  Redis Commander: http://localhost:8081"

# ============== Development Commands ==============

venv:
	@echo "$(BLUE)🐍 Creating Python virtual environment...$(NC)"
	@python3 -m venv .venv
	@echo "$(GREEN)✅ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source .venv/bin/activate$(NC)"

install:
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

migrate-up:
	@echo "$(BLUE)🔄 Running database migrations...$(NC)"
	@if [ -d "migrations" ]; then \
		for file in migrations/*.sql; do \
			if [ -f "$$file" ]; then \
				echo "$(YELLOW)Running: $$file$(NC)"; \
				PGPASSWORD=coupon_pass psql -h localhost -U coupon_user -d coupon_db -f "$$file" 2>&1 | grep -v "already exists" || true; \
			fi \
		done; \
		echo "$(GREEN)✅ Migrations complete$(NC)"; \
	else \
		echo "$(RED)❌ migrations/ directory not found$(NC)"; \
	fi

docker-migrate:
	@bash scripts/docker_migrate.sh

seed-db:
	@echo "$(BLUE)🌱 Seeding database...$(NC)"
	@.venv/bin/python scripts/seed_regions_countries.py
	@echo "$(GREEN)✅ Database seeded$(NC)"

create-admin-local:
	@echo "$(BLUE)👤 Creating admin user...$(NC)"
	@.venv/bin/python create_admin.py
	@echo "$(GREEN)✅ Admin user created$(NC)"

run:
	@echo "$(BLUE)🚀 Starting application...$(NC)"
	@.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "$(BLUE)🔥 Starting development server with auto-reload...$(NC)"
	@echo "$(GREEN)📖 API Docs: http://localhost:8000/docs$(NC)"
	@.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@.venv/bin/pytest -v

test-coverage:
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	@.venv/bin/pytest --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/index.html$(NC)"

clean:
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# ============== Production Commands ==============

deploy:
	@echo "🚀 Redeploying..."
	./deploy.sh

redeploy: deploy

logs:
	@echo "📋 Viewing all logs..."
	docker logs -f coupon-api-container

logs-webhook:
	@echo "🔔 Viewing webhook logs..."
	docker logs -f coupon-api-container 2>&1 | grep --line-buffered WEBHOOK

logs-errors:
	@echo "❌ Viewing error logs..."
	docker logs -f coupon-api-container 2>&1 | grep --line-buffered -i error

shell:
	@echo "🐚 Entering container..."
	docker exec -it coupon-api-container /bin/bash

status:
	@docker ps -f name=coupon-api-container

stop:
	@echo "🛑 Stopping container..."
	docker stop coupon-api-container

restart:
	@echo "🔄 Restarting container..."
	docker restart coupon-api-container

clean-db:
	@echo "⚠️  Resetting Database (inside container)..."
	@echo "NOTE: You must 'make deploy' first if scripts/ was just added."
	docker exec -it coupon-api-container python scripts/reset_db.py

create-admin:
	@echo "👤 Creating Admin User..."
	docker exec -it coupon-api-container python create_admin.py --manual

seed-data:
	@echo "🌱 Seeding regions and countries..."
	docker exec -it coupon-api-container python scripts/seed_regions_countries.py

migrate:
	@echo "🔄 Running database migrations..."
	@echo "Note: Run 'make deploy' first to ensure latest code is on server"
	@echo ""
	@echo "Running migration: 015_add_currency_to_orders.sql"
	@cat migrations/015_add_currency_to_orders.sql | docker exec -i coupon-api-container psql $$DATABASE_URL
	@echo ""
	@echo "✅ Migration complete - Run 'make restart' to apply changes"

test:
	pytest

install:
	pip install -r requirements.txt

run-local:
	uvicorn app.main:app --reload --port 8000

setup-load-test:
	@echo "📦 Installing load testing tools..."
	pip install locust requests

benchmark-simple:
	@echo "⚡ Running simple benchmark (curl only)..."
	@bash scripts/simple_benchmark.sh https://api.vouchergalaxy.com /health

load-test:
	@echo "🔥 Starting Load Test (Web UI)..."
	@echo "Open http://localhost:8089 in your browser"
	@echo "Target: https://api.vouchergalaxy.com"
	locust -f tests/load_test.py --host=https://api.vouchergalaxy.com

load-test-headless:
	@echo "🔥 Running Load Test (Headless Mode)..."
	@echo "Target: https://api.vouchergalaxy.com"
	@echo "Users: 2000, Spawn Rate: 100/sec, Duration: 2 minutes"
	locust -f tests/load_test.py --host=https://api.vouchergalaxy.com \
		--users 2000 --spawn-rate 100 --run-time 2m --headless

benchmark:
	@echo "⚡ Quick Benchmark..."
	@echo "Target: https://api.vouchergalaxy.com"
	@echo "Users: 100, Spawn Rate: 10/sec, Duration: 1 minute"
	locust -f tests/load_test.py --host=https://api.vouchergalaxy.com \
		--users 100 --spawn-rate 10 --run-time 1m --headless
