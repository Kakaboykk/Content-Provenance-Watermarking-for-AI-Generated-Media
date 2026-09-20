"""
backend/app/models/provenance.py

ORM model for the provenance_records table.

A provenance record is created at AI-generation time and carries all
metadata about who generated the image, which model/provider was used,
and any extra structured metadata.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    # Primary key: internal serial UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The UUID that is actually embedded into the watermark payload.
    # Must be globally unique — the watermark extraction returns this value.
    provenance_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        comment="UUID embedded in the watermark payload",
    )

    # Source of the image (e.g. 'ai_generated', 'human_uploaded')
    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Origin type: ai_generated | human_uploaded | unknown",
    )

    # AI-generation details (nullable because not always applicable)
    generation_provider: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="Provider name, e.g. 'openai', 'stability-ai'",
    )
    model_name: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="Model identifier, e.g. 'dall-e-3', 'stable-diffusion-xl'",
    )
    prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Generation prompt (may be long)",
    )

    # Flexible structured metadata (tags, parameters, etc.)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        name="metadata",
        comment="Arbitrary structured metadata as JSON/JSONB",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Record creation timestamp (UTC)",
    )

    # Relationship: one provenance record → many watermarked assets
    watermarked_assets: Mapped[list["WatermarkedAsset"]] = relationship(  # noqa: F821
        "WatermarkedAsset",
        back_populates="provenance_record",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ProvenanceRecord id={self.id} "
            f"provenance_uuid={self.provenance_uuid} "
            f"source_type={self.source_type!r}>"
        )
