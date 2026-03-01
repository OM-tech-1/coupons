# Docker Setup Summary

## Files Created

1. **docker-compose.yml** - Docker services configuration
2. **.env.docker** - Environment template for Docker
3. **DOCKER_SETUP.md** - Comprehensive setup guide
4. **docker-start.sh** - Quick start script

## Quick Start

```bash
# Make script executable (already done)
chmod +x docker-start.sh

# Run the setup script
./docker-start.sh
```

## What's Included

### Services

- **PostgreSQL 15** (port 5432)
  - User: `coupon_user`
  - Password: `coupon_pass`
  - Database: `coupon_db`

- **Redis 7** (port 6379)
  - No authentication
  - Persistent storage

### Optional Tools

```bash
docker-compose --profile tools up -d
```

- **pgAdmin** (port 5050) - PostgreSQL web UI
- **Redis Commander** (port 8081) - Redis web UI

## Backend Compatibility

### ✅ Works WITHOUT Redis

The backend has graceful fallback and will work without Redis:

- All API endpoints function normally
- Database operations work fine
- Authentication and authorization work
- Payments and orders work

### ⚠️ Degraded WITHOUT Redis

- No caching (slower response times)
- Trending coupons fall back to newest
- Recently viewed feature disabled
- Stock tracking uses database only

### How It Works

The `app/cache.py` module checks Redis availability:

```python
def get_redis_client():
    try:
        _redis_client = redis.from_url(redis_url)
        _redis_client.ping()
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable. Caching disabled.")
        return None  # Graceful degradation
```

All Redis operations handle `None` client:

```python
def get_cache(key):
    client = get_redis_client()
    if client is None:
        return None  # Cache miss, query DB
    # ... Redis operations
```

## Database Switching

### Current Setup (Supabase)

```bash
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

### Switch to Docker

1. Update `.env`:
```bash
DATABASE_URL=postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db
REDIS_URL=redis://localhost:6379/0
```

2. Start Docker:
```bash
./docker-start.sh
```

3. Run migrations:
```bash
python -m alembic upgrade head
```

4. Restart app:
```bash
uvicorn app.main:app --reload
```

### Switch Back to Supabase

1. Update `.env` with Supabase URL
2. Restart app (no migrations needed)

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Connect to PostgreSQL
docker exec -it coupon_postgres psql -U coupon_user -d coupon_db

# Connect to Redis
docker exec -it coupon_redis redis-cli

# Check service status
docker-compose ps
```

## Testing

The Docker setup is perfect for:

- Local development
- Running tests with fresh database
- Testing migrations
- Performance testing with Redis
- Integration testing

## Production Note

⚠️ **This setup is for LOCAL DEVELOPMENT ONLY**

For production, use:
- Managed PostgreSQL (AWS RDS, Supabase, etc.)
- Managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- Proper security (SSL, strong passwords, firewalls)
- Backup strategies
- Monitoring and alerting

## Troubleshooting

### Port conflicts
```bash
# Change ports in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 instead of 5432
```

### Services not starting
```bash
# Check logs
docker-compose logs postgres
docker-compose logs redis

# Restart
docker-compose restart
```

### Clean slate
```bash
# Remove everything and start fresh
docker-compose down -v
./docker-start.sh
```

## Next Steps

1. ✅ Docker services created
2. ✅ Environment template created
3. ✅ Documentation written
4. ⏭️ Run `./docker-start.sh` to start
5. ⏭️ Run migrations
6. ⏭️ Start developing!
