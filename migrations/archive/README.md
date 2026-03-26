# Archived SQL Migrations

These SQL files are **historical only** and are **no longer executed**.

All schema changes they describe are now consolidated in the single Alembic baseline migration:

**`migrations/alembic/versions/0001_baseline.py`**

## Why they were archived

The project migrated from manual SQL files to **Alembic** for proper version tracking. Alembic maintains an `alembic_version` table in the database so that:
- Each migration runs exactly once
- Deployments fail loudly if a migration fails (instead of silently skipping)
- New migrations are easy to add with `alembic revision -m "description"`

## How to add future migrations

```bash
# Generate a new migration file
alembic revision -m "add_foo_column_to_bar_table"

# Edit the generated file in migrations/alembic/versions/
# then apply it:
alembic upgrade head
```

## Do NOT re-run these files

Running any of these SQL files against the database will produce errors or duplicate operations. They exist here only as a historical record.
