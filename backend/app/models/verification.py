"""
backend/app/models/verification.py

ORM model for the verification_records table.

A verification record is created each time someone submits an image for
watermark extraction. It is intentionally decoupled from watermarked_assets
because a submitted image may or may not carry a known watermark.

Verdict values are exactly those defined by the frozen specification:
  AUTHENTIC_UNMODIFIED
  TRACED_BUT_MODIFIED
  WATERMARK_UNRECOVERABLE
  NO_WATERMARK_FOUND
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Frozen verdict values — must match watermark/extract.py exactly
VALID_VERDICTS = frozenset(
    {
        "AUTHENTIC_UNMODIFIED",
        "TRACED_BUT_MODIFIED",
        "WATERMARK_UNRECOVERABLE",
        "NO_WATERMARK_FOUND",
    }
)


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # SHA-256 of the image that was submitted for verification
    submitted_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hex digest of the submitted image",
    )

    # UUID recovered from the watermark (NULL when extraction fails)
    extracted_provenance_uuid: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Watermark UUID recovered from the image; NULL on failure",
    )

    # One of the four frozen verdict values
    verdict: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment=(
            "Extraction outcome: AUTHENTIC_UNMODIFIED | TRACED_BUT_MODIFIED | "
            "WATERMARK_UNRECOVERABLE | NO_WATERMARK_FOUND"
        ),
    )

    # Optional structured details (BER, ECC result, PSNR, etc.)
    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Structured extraction diagnostics as JSON",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<VerificationRecord id={self.id} "
            f"verdict={self.verdict!r} "
            f"extracted_uuid={self.extracted_provenance_uuid}>"
        )
