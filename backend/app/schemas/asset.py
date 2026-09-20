"""
backend/app/schemas/asset.py

Pydantic v2 schemas for WatermarkedAsset.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WatermarkedAssetCreate(BaseModel):
    """Fields accepted when recording a new watermarked asset."""
    provenance_record_id: uuid.UUID
    sha256: str = Field(..., min_length=64, max_length=64)
    original_filename: str | None = Field(None, max_length=512)
    mime_type: str = Field("image/png", max_length=64)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    watermark_delta: float = Field(..., gt=0)


class WatermarkedAssetRead(BaseModel):
    """Fields returned when reading a watermarked asset."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provenance_record_id: uuid.UUID
    sha256: str
    original_filename: str | None
    mime_type: str
    width: int
    height: int
    watermark_delta: float
    created_at: datetime
