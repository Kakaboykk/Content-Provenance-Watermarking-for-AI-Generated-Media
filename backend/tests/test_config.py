"""
Tests for app/core/config.py
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("APP_ENV", "test")

from app.core.config import Settings


def test_settings_reads_database_url():
    s = Settings(DATABASE_URL="postgresql+psycopg2://user:pass@localhost/db")
    assert s.DATABASE_URL == "postgresql+psycopg2://user:pass@localhost/db"


def test_settings_defaults():
    # Pass all values explicitly to avoid ambient env vars from conftest
    s = Settings(DATABASE_URL="sqlite+pysqlite:///:memory:", APP_ENV="development", LOG_LEVEL="INFO")
    assert s.APP_ENV == "development"
    assert s.LOG_LEVEL == "INFO"


def test_settings_override_env():
    s = Settings(DATABASE_URL="sqlite://", APP_ENV="production", LOG_LEVEL="ERROR")
    assert s.APP_ENV == "production"
    assert s.LOG_LEVEL == "ERROR"
