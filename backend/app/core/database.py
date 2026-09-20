"""
backend/app/core/database.py

SQLAlchemy 2.x engine + session factory.

Usage in FastAPI routes:
    from app.core.database import get_db
    ...
    def my_route(db: Session = Depends(get_db)):
        ...
"""
import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings suitable for a development/test environment.
    # Tune pool_size / max_overflow for production.
    pool_pre_ping=True,   # Detects and discards stale connections
    echo=(settings.APP_ENV == "development"),  # Log SQL in dev mode
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # avoid lazy-load issues after commit
)

# ---------------------------------------------------------------------------
# Declarative base — all ORM models must inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass

# ---------------------------------------------------------------------------
# FastAPI dependency — yields a session and guarantees cleanup
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yield a database session; ensure it is closed after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Health-check helper
# ---------------------------------------------------------------------------
def check_db_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False
