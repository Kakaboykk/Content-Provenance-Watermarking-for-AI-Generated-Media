"""
backend/app/schemas/verification.py

Pydantic v2 schemas for VerificationRecord.
"""
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

VerdictLiteral = Literal[
    "AUTHENTIC_UNMODIFIED",
    "TRACED_BUT_MODIFIED",
    "WATERMARK_UNRECOVERABLE",
    "NO_WATERMARK_FOUND",
]


class VerificationRecordCreate(BaseModel):
    """Fields accepted when storing a verification result."""
    submitted_sha256: str = Field(..., min_length=64, max_length=64)
    extracted_provenance_uuid: uuid.UUID | None = None
    verdict: VerdictLiteral
    details: dict[str, Any] | None = None


class VerificationRecordRead(BaseModel):
    """Fields returned when reading a verification record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submitted_sha256: str
    extracted_provenance_uuid: uuid.UUID | None
    verdict: str
    details: dict[str, Any] | None
    created_at: datetime
