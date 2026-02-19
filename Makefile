# Makefile for Coupon API

.PHONY: help deploy redeploy logs shell stop restart status clean-db create-admin test install run-local

help:
	@echo "Coupon API Management"
	@echo "---------------------"
	@echo "make deploy       - Pull latest code and redeploy container (PROD)"
	@echo "make logs         - View live logs from container"
	@echo "make shell        - Open bash shell inside running container"
	@echo "make status       - Check container status"
	@echo "make stop         - Stop the container"
	@echo "make restart      - Restart the container"
	@echo "make clean-db     - Reset database (Drop & Create tables) - Interactive"
	@echo "make create-admin - Create/Promote admin user (inside container)"
	@echo "make test         - Run tests locally"
	@echo "make install      - Install local dependencies"
	@echo "make run-local    - Run app locally with hot reload"

deploy:
	@echo "🚀 Redeploying..."
	./deploy.sh

redeploy: deploy

logs:
	@echo "Combine logs..."
	docker logs -f coupon-api-container

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
	docker exec -it coupon-api-container python create_admin.py

test:
	pytest

install:
	pip install -r requirements.txt

run-local:
	uvicorn app.main:app --reload --port 8000
