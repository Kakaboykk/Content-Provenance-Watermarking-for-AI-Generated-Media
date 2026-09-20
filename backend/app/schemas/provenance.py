"""
backend/app/schemas/provenance.py

Pydantic v2 schemas for ProvenanceRecord.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceRecordCreate(BaseModel):
    """Fields accepted when creating a new provenance record."""
    source_type: str = Field(..., max_length=64, examples=["ai_generated"])
    generation_provider: str | None = Field(None, max_length=128)
    model_name: str | None = Field(None, max_length=256)
    prompt: str | None = None
    metadata_json: dict[str, Any] | None = None


class ProvenanceRecordRead(BaseModel):
    """Fields returned when reading a provenance record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provenance_uuid: uuid.UUID
    source_type: str
    generation_provider: str | None
    model_name: str | None
    prompt: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
