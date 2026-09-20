"""
backend/app/models/__init__.py

Import all models here so that Alembic's env.py can import them via
a single `from app.models import *` or `import app.models`.
"""
from app.models.provenance import ProvenanceRecord  # noqa: F401
from app.models.asset import WatermarkedAsset  # noqa: F401
from app.models.verification import VerificationRecord  # noqa: F401

__all__ = ["ProvenanceRecord", "WatermarkedAsset", "VerificationRecord"]
