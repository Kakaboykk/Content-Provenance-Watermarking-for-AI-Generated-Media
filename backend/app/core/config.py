"""
backend/app/core/config.py

Centralised settings loaded from environment variables / .env file.
All other modules must import settings from here — never read
os.environ directly in business code.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Values are loaded (in order of priority):
      1. Environment variables
      2. A .env file in the backend/ directory
      3. The field defaults defined below
    """

    # ---- Database --------------------------------------------------------
    DATABASE_URL: str
    # e.g. postgresql+psycopg2://postgres:changeme@localhost:5432/content_provenance

    # ---- Application -----------------------------------------------------
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",          # relative to the working directory (backend/)
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Single shared instance — import this everywhere
settings = Settings()  # type: ignore[call-arg]
