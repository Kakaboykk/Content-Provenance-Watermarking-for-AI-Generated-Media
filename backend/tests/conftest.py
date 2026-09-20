"""
backend/tests/conftest.py

Shared pytest fixtures for backend tests.

These tests use an in-memory SQLite database so they run without a real
PostgreSQL instance.  The health-check endpoint is tested via the ASGI
test client (no running server needed).
"""
import os
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Point to a SQLite in-memory DB so tests never need PostgreSQL
os.environ.setdefault(
    "DATABASE_URL", "sqlite+pysqlite:///:memory:"
)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# In-memory SQLite engine + session for tests
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+pysqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DB_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    """Provide a transactional session that is rolled back after each test."""
    TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client with DB dependency overridden to use test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
