# Makefile for Coupon API

.PHONY: help deploy redeploy logs logs-webhook logs-errors shell stop restart status clean-db create-admin seed-data migrate test install run-local setup-load-test load-test load-test-headless benchmark benchmark-simple

help:
	@echo "Coupon API Management"
	@echo "---------------------"
	@echo "make deploy           - Pull latest code and redeploy container (PROD)"
	@echo "make logs             - View live logs from container"
	@echo "make logs-webhook     - View webhook logs only"
	@echo "make logs-errors      - View error logs only"
	@echo "make shell            - Open bash shell inside running container"
	@echo "make status           - Check container status"
	@echo "make stop             - Stop the container"
	@echo "make restart          - Restart the container"
	@echo "make clean-db         - Reset database (Drop & Create tables) - Interactive"
	@echo "make create-admin     - Create/Promote admin user (inside container)"
	@echo "make seed-data        - Seed regions and countries into database"
	@echo "make migrate          - Run pending database migrations"
	@echo "make test             - Run tests locally"
	@echo "make install          - Install local dependencies"
	@echo "make run-local        - Run app locally with hot reload"
	@echo ""
	@echo "Load Testing:"
	@echo "make setup-load-test  - Install locust for load testing"
	@echo "make benchmark-simple - Simple benchmark (curl only, no install)"
	@echo "make load-test        - Run load test (interactive web UI)"
	@echo "make load-test-headless - Run load test (headless, 2000 users)"
	@echo "make benchmark        - Quick benchmark (100 users, 1 min)"

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
