#!/bin/bash

# Setup Verification Script
# Checks if the development environment is properly configured

set -e

echo "🔍 Verifying Development Environment Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        echo -e "${GREEN}✓${NC} Docker $DOCKER_VERSION (running)"
    else
        echo -e "${YELLOW}⚠${NC} Docker installed but not running"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗${NC} Docker not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker Compose
echo -n "Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
    echo -e "${GREEN}✓${NC} Docker Compose $COMPOSE_VERSION"
else
    echo -e "${RED}✗${NC} Docker Compose not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Make
echo -n "Checking Make... "
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n1 | cut -d' ' -f3)
    echo -e "${GREEN}✓${NC} Make $MAKE_VERSION"
else
    echo -e "${RED}✗${NC} Make not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Git
echo -n "Checking Git... "
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo -e "${GREEN}✓${NC} Git $GIT_VERSION"
else
    echo -e "${RED}✗${NC} Git not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Checking Project Files..."

# Check virtual environment
echo -n "Checking virtual environment... "
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${NC} .venv exists"
else
    echo -e "${YELLOW}⚠${NC} .venv not found (run: make venv)"
fi

# Check .env file
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env exists"
else
    echo -e "${YELLOW}⚠${NC} .env not found (run: make docker-setup)"
fi

# Check Docker services
echo ""
echo "Checking Docker Services..."

echo -n "Checking PostgreSQL... "
if docker ps | grep -q coupon_postgres; then
    if docker exec coupon_postgres pg_isready -U coupon_user -d coupon_db &> /dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL running and ready"
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL running but not ready"
    fi
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL not running (run: make docker-up)"
fi

echo -n "Checking Redis... "
if docker ps | grep -q coupon_redis; then
    if docker exec coupon_redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis running and ready"
    else
        echo -e "${YELLOW}⚠${NC} Redis running but not ready"
    fi
else
    echo -e "${YELLOW}⚠${NC} Redis not running (run: make docker-up)"
fi

# Check Python packages
echo ""
echo "Checking Python Packages..."

if [ -d ".venv" ]; then
    echo -n "Checking FastAPI... "
    if .venv/bin/python -c "import fastapi" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} FastAPI installed"
    else
        echo -e "${YELLOW}⚠${NC} FastAPI not installed (run: make install)"
    fi

    echo -n "Checking SQLAlchemy... "
    if .venv/bin/python -c "import sqlalchemy" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} SQLAlchemy installed"
    else
        echo -e "${YELLOW}⚠${NC} SQLAlchemy not installed (run: make install)"
    fi

    echo -n "Checking Pytest... "
    if .venv/bin/python -c "import pytest" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Pytest installed"
    else
        echo -e "${YELLOW}⚠${NC} Pytest not installed (run: make install)"
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All required tools are installed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: make setup"
    echo "  2. Run: make dev"
    echo "  3. Open: http://localhost:8000/docs"
else
    echo -e "${RED}❌ Found $ERRORS error(s)${NC}"
    echo ""
    echo "Please install missing tools and try again."
fi
echo "=========================================="
