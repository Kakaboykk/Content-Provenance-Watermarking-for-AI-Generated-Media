"""
backend/app/services/asset.py

Service layer for watermarked asset registration.

Responsibilities:
  - Calculate SHA-256 hash of the final watermarked image bytes.
  - Create the `watermarked_assets` database record, linking it to its provenance record.
  - Roll back cleanly on DB error.
"""
import hashlib
import io
import logging
import uuid
from typing import Any

from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.asset import WatermarkedAsset
from app.schemas.asset import WatermarkedAssetCreate, WatermarkedAssetRead
from watermark.config import DELTA_INITIAL

logger = logging.getLogger(__name__)


class AssetServiceError(Exception):
    """Raised when the asset service fails to complete an operation."""


def register_watermarked_asset(
    db: Session,
    provenance_record_id: uuid.UUID,
    image_bytes: bytes,
    original_filename: str | None = None,
    delta: float = DELTA_INITIAL,
) -> WatermarkedAssetRead:
    """
    Compute SHA-256 from raw bytes and register the asset in the database.

    Args:
        db: Active SQLAlchemy session.
        provenance_record_id: The `id` (not `provenance_uuid`) of the ProvenanceRecord.
        image_bytes: The raw bytes of the watermarked PNG image.
        original_filename: Optional original filename supplied by the client.
        delta: The watermark embedding strength used.

    Returns:
        WatermarkedAssetRead — populated record as stored in the DB.

    Raises:
        AssetServiceError: If image processing or database insertion fails.
    """
    if not image_bytes:
        raise AssetServiceError("Empty image bytes provided.")

    # 1. Compute SHA-256
    hasher = hashlib.sha256()
    hasher.update(image_bytes)
    sha256_hex = hasher.hexdigest()

    # 2. Extract dimensions from the bytes to ensure accuracy
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
    except Exception as exc:
        raise AssetServiceError(f"Failed to read image dimensions from bytes: {exc}") from exc

    # 3. Prepare the DB model
    record = WatermarkedAsset(
        provenance_record_id=provenance_record_id,
        sha256=sha256_hex,
        original_filename=original_filename,
        mime_type="image/png",  # We always output lossless PNGs from the watermark engine
        width=width,
        height=height,
        watermark_delta=delta,
    )

    # 4. Persist
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "WatermarkedAsset registered: id=%s sha256=%s provenance_id=%s",
            record.id,
            record.sha256,
            record.provenance_record_id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to register WatermarkedAsset: %s", exc)
        raise AssetServiceError(
            f"Database error while registering asset: {exc}"
        ) from exc

    return WatermarkedAssetRead.model_validate(record)


def get_asset_by_sha256(
    db: Session,
    sha256_hex: str,
) -> WatermarkedAssetRead | None:
    """
    Retrieve an asset record by its SHA-256 hash.
    Returns None if not found.
    """
    record = (
        db.query(WatermarkedAsset)
        .filter(WatermarkedAsset.sha256 == sha256_hex)
        .order_by(WatermarkedAsset.created_at.desc())
        .first()
    )
    if record is None:
        return None
    return WatermarkedAssetRead.model_validate(record)
