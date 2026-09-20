"""
backend/tests/test_asset_service.py

Automated tests for the asset registration service (Phase 2B-4).
"""
import hashlib
import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.asset import WatermarkedAsset
from app.models.provenance import ProvenanceRecord
from app.services.asset import AssetServiceError, register_watermarked_asset, get_asset_by_sha256
from app.schemas.asset import WatermarkedAssetRead
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.provenance import create_provenance_record


# 1x1 transparent PNG for testing
MINIMAL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15"
    b"\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x60\x00\x02\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def dummy_provenance(db_session):
    data = ProvenanceRecordCreate(source_type="ai_generated")
    return create_provenance_record(db_session, data)


class TestRegisterWatermarkedAsset:

    def test_successful_registration(self, db_session, dummy_provenance):
        result = register_watermarked_asset(
            db_session,
            provenance_record_id=dummy_provenance.id,
            image_bytes=MINIMAL_PNG_BYTES,
            original_filename="test.png",
        )

        assert isinstance(result, WatermarkedAssetRead)
        assert result.id is not None
        assert result.provenance_record_id == dummy_provenance.id
        assert result.original_filename == "test.png"
        assert result.mime_type == "image/png"
        assert result.width == 1
        assert result.height == 1
        assert result.watermark_delta == 30.0
        
        # Verify SHA-256 calculation
        expected_sha = hashlib.sha256(MINIMAL_PNG_BYTES).hexdigest()
        assert result.sha256 == expected_sha

    def test_empty_bytes_raises_error(self, db_session, dummy_provenance):
        with pytest.raises(AssetServiceError) as exc:
            register_watermarked_asset(
                db_session,
                provenance_record_id=dummy_provenance.id,
                image_bytes=b"",
            )
        assert "Empty image bytes" in str(exc.value)

    def test_invalid_image_bytes_raises_error(self, db_session, dummy_provenance):
        with pytest.raises(AssetServiceError) as exc:
            register_watermarked_asset(
                db_session,
                provenance_record_id=dummy_provenance.id,
                image_bytes=b"not an image",
            )
        assert "Failed to read image dimensions" in str(exc.value)

    def test_foreign_key_constraint(self, db_session):
        # Using a nonexistent provenance ID should raise AssetServiceError
        # (which wraps the SQLAlchemy IntegrityError)
        nonexistent_id = uuid.uuid4()
        
        with pytest.raises(AssetServiceError) as exc:
            register_watermarked_asset(
                db_session,
                provenance_record_id=nonexistent_id,
                image_bytes=MINIMAL_PNG_BYTES,
            )
        assert "Database error" in str(exc.value)
        assert "FOREIGN KEY constraint failed" in str(exc.value)


class TestGetAssetBySha256:

    def test_returns_existing_record(self, db_session, dummy_provenance):
        created = register_watermarked_asset(
            db_session,
            provenance_record_id=dummy_provenance.id,
            image_bytes=MINIMAL_PNG_BYTES,
        )

        fetched = get_asset_by_sha256(db_session, created.sha256)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.provenance_record_id == created.provenance_record_id

    def test_returns_none_for_unknown_sha256(self, db_session):
        fetched = get_asset_by_sha256(db_session, "0" * 64)
        assert fetched is None
