"""
backend/app/services/provenance.py

Service layer for provenance record creation.

Responsibilities:
  - Generate the provenance UUID (the one that will be embedded in the watermark)
  - Accept caller-supplied metadata
  - Persist the record using the SQLAlchemy session passed in
  - Commit on success, roll back on failure, re-raise so the caller decides
    how to respond

This module does NOT:
  - open its own database sessions (always accepts a session from the caller)
  - perform image processing or watermark embedding (future phase)
  - know about HTTP or FastAPI (pure Python service)
"""
import logging
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.provenance import ProvenanceRecord
from app.schemas.provenance import ProvenanceRecordCreate, ProvenanceRecordRead

logger = logging.getLogger(__name__)


class ProvenanceServiceError(Exception):
    """Raised when the provenance service cannot complete an operation."""


def create_provenance_record(
    db: Session,
    data: ProvenanceRecordCreate,
) -> ProvenanceRecordRead:
    """
    Create and persist a single provenance record.

    Args:
        db:   An active SQLAlchemy session (caller is responsible for scope).
        data: Validated input data (Pydantic ProvenanceRecordCreate).

    Returns:
        ProvenanceRecordRead — the fully populated record as stored in the DB.

    Raises:
        ProvenanceServiceError: if the database operation fails, after rolling
            back the transaction.
    """
    # Generate the UUID that will ultimately be embedded in the watermark.
    # We generate it here so the service owns the provenance UUID lifecycle.
    provenance_uuid = uuid.uuid4()

    record = ProvenanceRecord(
        provenance_uuid=provenance_uuid,
        source_type=data.source_type,
        generation_provider=data.generation_provider,
        model_name=data.model_name,
        prompt=data.prompt,
        metadata_json=data.metadata_json,
        # created_at is set by the ORM default (datetime.now(utc))
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)   # load DB-generated values (id, created_at)
        logger.info(
            "ProvenanceRecord created: id=%s provenance_uuid=%s source_type=%r",
            record.id,
            record.provenance_uuid,
            record.source_type,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create ProvenanceRecord: %s", exc)
        raise ProvenanceServiceError(
            f"Database error while creating provenance record: {exc}"
        ) from exc

    return ProvenanceRecordRead.model_validate(record)


def get_provenance_record_by_uuid(
    db: Session,
    provenance_uuid: uuid.UUID,
) -> ProvenanceRecordRead | None:
    """
    Retrieve a provenance record by its provenance_uuid (the watermark UUID).

    Returns None if no record is found.
    """
    record = (
        db.query(ProvenanceRecord)
        .filter(ProvenanceRecord.provenance_uuid == provenance_uuid)
        .one_or_none()
    )
    if record is None:
        return None
    return ProvenanceRecordRead.model_validate(record)
