#!/bin/bash
# scripts/docker_migrate.sh
# Runs database migrations inside the Docker PostgreSQL container
# This is useful for users who don't have psql installed locally.
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 Running database migrations inside Docker...${NC}"

if [ ! -d "migrations" ]; then
    echo -e "${RED}❌ migrations/ directory not found${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Initializing database schema...${NC}"
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python scripts/init_db.py
else
    python scripts/init_db.py
fi

for file in migrations/*.sql; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Running: $file${NC}"
        # Execute the SQL file inside the coupon_postgres container
        cat "$file" | docker exec -i coupon_postgres psql -U coupon_user -d coupon_db 2>&1 | grep -v "already exists" || true
    fi
done

echo -e "${GREEN}✅ Migrations complete${NC}"
