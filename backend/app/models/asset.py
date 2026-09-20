"""
backend/app/models/asset.py

ORM model for the watermarked_assets table.

Each row represents one watermarked image file that was produced from a
ProvenanceRecord.  Binary image data is NOT stored here — only metadata.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WatermarkedAsset(Base):
    __tablename__ = "watermarked_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key back to the provenance record that owns this asset
    provenance_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provenance_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hex digest of the watermarked PNG file (64 hex characters)
    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hex digest of the saved watermarked PNG",
    )

    original_filename: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Original filename provided by the client (for display only)",
    )

    mime_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="image/png",
        comment="MIME type of the stored file",
    )

    # Canonical dimensions after preprocessing (always 512×512 for Phase 0)
    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Width in pixels of the watermarked image",
    )
    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Height in pixels of the watermarked image",
    )

    # The QIM Delta value that was actually used during embedding
    watermark_delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="QIM Delta value used during watermark embedding",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship back to provenance record
    provenance_record: Mapped["ProvenanceRecord"] = relationship(  # noqa: F821
        "ProvenanceRecord",
        back_populates="watermarked_assets",
    )

    def __repr__(self) -> str:
        return (
            f"<WatermarkedAsset id={self.id} "
            f"sha256={self.sha256[:12]}... "
            f"delta={self.watermark_delta}>"
        )
