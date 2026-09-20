"""
backend/alembic/env.py

Alembic environment configuration.

Key behaviours:
  - Reads DATABASE_URL from the .env file (or environment) via app.core.config.settings
  - Imports all ORM models via app.models so Alembic can detect table changes
  - Supports both online (live DB) and offline (SQL-script) migration modes
"""
from __future__ import annotations

import sys
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Ensure 'backend/' is on sys.path so that 'app' is importable
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# Load .env before importing settings (python-dotenv)
# ---------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

# ---------------------------------------------------------------------------
# Import settings & models
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402
import app.models  # noqa: E402, F401  — registers all ORM models
from app.core.database import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic Config object (provides access to values in alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url with the value from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure logging from alembic.ini if a logging section is present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Emit SQL statements to stdout without connecting to the database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Connect to the database and run migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
