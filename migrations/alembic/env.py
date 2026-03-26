import os
import sys

# Ensure the project root (/app inside Docker) is on sys.path so
# `from app.models import ...` works regardless of where alembic is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# ──────────────────────────────────────────────────────────────────
# Load .env so DATABASE_URL is available when running via CLI
# ──────────────────────────────────────────────────────────────────
load_dotenv()

# ──────────────────────────────────────────────────────────────────
# Alembic Config object – gives access to the values within alembic.ini
# ──────────────────────────────────────────────────────────────────
config = context.config

# Inject DATABASE_URL from environment into Alembic config
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Cannot run Alembic migrations."
    )
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ──────────────────────────────────────────────────────────────────
# Import the SQLAlchemy Base so autogenerate can diff against models
# ──────────────────────────────────────────────────────────────────
# NOTE: All models must be imported BEFORE this import so that
# Base.metadata contains every table.
from app.models import (  # noqa: F401, E402
    User, Coupon, UserCoupon, CartItem, Order, Payment, PaymentToken,
    Category, Region, Country, Package, PackageCoupon,
)
from app.models.contact_message import ContactMessage  # noqa: F401, E402
from app.database import Base  # noqa: E402

target_metadata = Base.metadata


# ──────────────────────────────────────────────────────────────────
# Migration runner – offline mode (generates SQL script)
# ──────────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This option configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ──────────────────────────────────────────────────────────────────
# Migration runner – online mode (applies to live DB)
# ──────────────────────────────────────────────────────────────────
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
