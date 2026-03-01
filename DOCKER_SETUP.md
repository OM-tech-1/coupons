# Docker Setup Guide

This guide explains how to run the Coupon App with Docker for local development and testing.

## Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 2. Configure Environment

```bash
# Copy Docker environment template
cp .env.docker .env

# Edit .env with your configuration (JWT secret, Stripe keys, etc.)
nano .env
```

### 3. Run Migrations

```bash
# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Run migrations
python -m alembic upgrade head

# Or run SQL migrations manually
psql postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db < migrations/001_initial_schema.sql
```

### 4. Seed Data (Optional)

```bash
# Seed regions and countries
python scripts/seed_regions_countries.py

# Create admin user
python create_admin.py
```

### 5. Start Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Services

### Core Services (Always Running)

- **PostgreSQL**: `localhost:5432`
  - Database: `coupon_db`
  - User: `coupon_user`
  - Password: `coupon_pass`

- **Redis**: `localhost:6379`
  - No authentication by default
  - Persistent storage enabled

### Optional Tools (Use `--profile tools`)

```bash
# Start with management tools
docker-compose --profile tools up -d
```

- **pgAdmin**: `http://localhost:5050`
  - Email: `admin@coupon.local`
  - Password: `admin`

- **Redis Commander**: `http://localhost:8081`
  - Web UI for Redis management

## Database Connection Strings

### PostgreSQL

```bash
# From host machine
postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db

# From another Docker container
postgresql://coupon_user:coupon_pass@postgres:5432/coupon_db
```

### Redis

```bash
# From host machine
redis://localhost:6379/0

# From another Docker container
redis://redis:6379/0
```

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart a service
docker-compose restart postgres
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it coupon_postgres psql -U coupon_user -d coupon_db

# Backup database
docker exec coupon_postgres pg_dump -U coupon_user coupon_db > backup.sql

# Restore database
docker exec -i coupon_postgres psql -U coupon_user coupon_db < backup.sql

# Check database size
docker exec coupon_postgres psql -U coupon_user -d coupon_db -c "SELECT pg_size_pretty(pg_database_size('coupon_db'));"
```

### Redis Operations

```bash
# Connect to Redis CLI
docker exec -it coupon_redis redis-cli

# Check Redis memory usage
docker exec coupon_redis redis-cli INFO memory

# Flush all Redis data (⚠️ clears cache)
docker exec coupon_redis redis-cli FLUSHALL

# Monitor Redis commands in real-time
docker exec coupon_redis redis-cli MONITOR
```

## Backend Behavior Without Redis

The backend is designed to work gracefully without Redis:

### ✅ What Works Without Redis

- All core API endpoints
- User authentication and authorization
- CRUD operations (coupons, packages, orders)
- Database queries
- Payment processing
- File uploads
- Admin dashboard

### ⚠️ What's Degraded Without Redis

- **Caching**: Database queries won't be cached (slower response times)
- **Trending Coupons**: Falls back to newest coupons
- **Recently Viewed**: Feature disabled
- **Stock Tracking**: Uses database only (slower updates)
- **Featured Coupons**: No caching (queries DB every time)

### How It Works

The `app/cache.py` module has built-in fallback logic:

```python
def get_redis_client():
    try:
        # Try to connect to Redis
        _redis_client = redis.from_url(redis_url)
        _redis_client.ping()
    except Exception as e:
        # If Redis fails, return None (graceful degradation)
        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        _redis_client = None
    return _redis_client
```

All Redis operations check if the client is available:

```python
def get_cache(key: str):
    client = get_redis_client()
    if client is None:
        return None  # Cache miss, query database
    # ... Redis operations
```

## Switching Between Databases

### From Supabase to Docker PostgreSQL

1. Update `.env`:
```bash
# Old (Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# New (Docker)
DATABASE_URL=postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db
```

2. Run migrations:
```bash
python -m alembic upgrade head
```

3. Restart application

### From Docker to Supabase

1. Update `.env` with Supabase URL
2. Restart application (no migrations needed if schema is same)

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 5432
lsof -i :5432

# Kill the process or change Docker port
# Edit docker-compose.yml: "5433:5432"
```

### Connection Refused

```bash
# Check if services are running
docker-compose ps

# Check service logs
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose restart
```

### Database Migration Errors

```bash
# Drop and recreate database
docker-compose down -v
docker-compose up -d
python -m alembic upgrade head
```

### Redis Connection Errors

```bash
# Check Redis is running
docker exec coupon_redis redis-cli ping
# Should return: PONG

# If not, restart Redis
docker-compose restart redis
```

## Production Considerations

⚠️ **This Docker setup is for LOCAL DEVELOPMENT ONLY**

For production:

1. Use managed services (AWS RDS, ElastiCache, Supabase)
2. Enable SSL/TLS for database connections
3. Use strong passwords and secrets
4. Enable Redis authentication
5. Configure proper backup strategies
6. Set up monitoring and alerting
7. Use connection pooling
8. Enable database replication

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Remove images
docker rmi postgres:15-alpine redis:7-alpine
```

## Additional Resources

- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
