"""Initial schema: provenance_records, watermarked_assets, verification_records

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-21 00:00:00.000000 UTC

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # provenance_records
    # ------------------------------------------------------------------
    op.create_table(
        "provenance_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="Internal primary key",
        ),
        sa.Column(
            "provenance_uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="UUID embedded in the watermark payload",
        ),
        sa.Column(
            "source_type",
            sa.String(64),
            nullable=False,
            comment="Origin type: ai_generated | human_uploaded | unknown",
        ),
        sa.Column(
            "generation_provider",
            sa.String(128),
            nullable=True,
            comment="Provider name, e.g. openai, stability-ai",
        ),
        sa.Column(
            "model_name",
            sa.String(256),
            nullable=True,
            comment="Model identifier, e.g. dall-e-3",
        ),
        sa.Column(
            "prompt",
            sa.Text,
            nullable=True,
            comment="Generation prompt",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Arbitrary structured metadata as JSONB",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Record creation timestamp (UTC)",
        ),
    )
    op.create_index(
        "ix_provenance_records_provenance_uuid",
        "provenance_records",
        ["provenance_uuid"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # watermarked_assets
    # ------------------------------------------------------------------
    op.create_table(
        "watermarked_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "provenance_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("provenance_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sha256",
            sa.String(64),
            nullable=False,
            comment="SHA-256 hex digest of the saved watermarked PNG",
        ),
        sa.Column(
            "original_filename",
            sa.String(512),
            nullable=True,
        ),
        sa.Column(
            "mime_type",
            sa.String(64),
            nullable=False,
            server_default="image/png",
        ),
        sa.Column(
            "width",
            sa.Integer,
            nullable=False,
            comment="Width in pixels",
        ),
        sa.Column(
            "height",
            sa.Integer,
            nullable=False,
            comment="Height in pixels",
        ),
        sa.Column(
            "watermark_delta",
            sa.Float,
            nullable=False,
            comment="QIM Delta used during embedding",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_watermarked_assets_provenance_record_id",
        "watermarked_assets",
        ["provenance_record_id"],
    )
    op.create_index(
        "ix_watermarked_assets_sha256",
        "watermarked_assets",
        ["sha256"],
    )

    # ------------------------------------------------------------------
    # verification_records
    # ------------------------------------------------------------------
    op.create_table(
        "verification_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "submitted_sha256",
            sa.String(64),
            nullable=False,
            comment="SHA-256 of the submitted image",
        ),
        sa.Column(
            "extracted_provenance_uuid",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Watermark UUID; NULL when extraction fails",
        ),
        sa.Column(
            "verdict",
            sa.String(32),
            nullable=False,
            comment=(
                "AUTHENTIC_UNMODIFIED | TRACED_BUT_MODIFIED | "
                "WATERMARK_UNRECOVERABLE | NO_WATERMARK_FOUND"
            ),
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Structured extraction diagnostics",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_verification_records_submitted_sha256",
        "verification_records",
        ["submitted_sha256"],
    )
    op.create_index(
        "ix_verification_records_extracted_provenance_uuid",
        "verification_records",
        ["extracted_provenance_uuid"],
    )

    # ------------------------------------------------------------------
    # Verdict CHECK constraint — enforce the four frozen values
    # ------------------------------------------------------------------
    op.create_check_constraint(
        "ck_verification_records_verdict",
        "verification_records",
        (
            "verdict IN ("
            "'AUTHENTIC_UNMODIFIED',"
            "'TRACED_BUT_MODIFIED',"
            "'WATERMARK_UNRECOVERABLE',"
            "'NO_WATERMARK_FOUND'"
            ")"
        ),
    )


def downgrade() -> None:
    op.drop_table("verification_records")
    op.drop_table("watermarked_assets")
    op.drop_table("provenance_records")
