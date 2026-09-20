"""
backend/app/services/verification.py

Service layer for watermark verification.
"""
import hashlib
import io
import logging
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.verification import VerificationRecord
from app.models.asset import WatermarkedAsset
from app.schemas.verification import VerificationRecordCreate, VerificationRecordRead
from watermark.extract import extract_watermark_with_stats

logger = logging.getLogger(__name__)


class VerificationServiceError(Exception):
    """Raised when the verification service fails unexpectedly."""


def verify_image_bytes(
    db: Session,
    image_bytes: bytes,
) -> VerificationRecordRead:
    """
    Verify the uploaded image by performing blind extraction.

    1. Compute SHA-256 of the submitted bytes.
    2. Extract watermark using Phase 0 engine.
    3. If extracted successfully ("AUTHENTIC_UNMODIFIED"), cross-reference with DB:
       If the SHA-256 is not registered, the image was edited/compressed,
       so downgrade verdict to "TRACED_BUT_MODIFIED".
    4. Save to `verification_records`.
    
    Returns:
        The created VerificationRecord (using the Pydantic Read schema).
    """
    if not image_bytes:
        raise VerificationServiceError("Empty image bytes provided.")

    # 1. Compute SHA-256
    hasher = hashlib.sha256()
    hasher.update(image_bytes)
    submitted_sha256 = hasher.hexdigest()

    # 2. Extract Watermark
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception as exc:
        raise VerificationServiceError(f"Failed to decode image bytes: {exc}") from exc

    try:
        verdict, extracted_uuid, stats = extract_watermark_with_stats(img)
    except Exception as exc:
        logger.error(f"Phase 0 extraction failed entirely: {exc}")
        raise VerificationServiceError("Fatal error during watermark extraction.") from exc

    # Serialize stats bytes (if candidate bytes exist) to hex for JSON storage
    if stats.get("candidate_bytes"):
        stats["candidate_bytes"] = stats["candidate_bytes"].hex()

    # 3. DB Cross-Reference for Modificaton Detection
    if verdict == "AUTHENTIC_UNMODIFIED":
        # Does this exact file (SHA-256) exist in our asset registry?
        asset_exists = db.query(WatermarkedAsset).filter_by(sha256=submitted_sha256).first() is not None
        if not asset_exists:
            # The UUID survived, but the file was altered (resized, compressed, etc)
            verdict = "TRACED_BUT_MODIFIED"

    # 4. Save to DB
    record = VerificationRecord(
        submitted_sha256=submitted_sha256,
        extracted_provenance_uuid=extracted_uuid,
        verdict=verdict,
        details=stats,
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "Verification complete: id=%s verdict=%s extracted_uuid=%s",
            record.id, verdict, extracted_uuid
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to save VerificationRecord: %s", exc)
        raise VerificationServiceError(f"Database error while saving verification record: {exc}") from exc

    return VerificationRecordRead.model_validate(record)
