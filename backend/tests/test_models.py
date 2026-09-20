"""
Tests for ORM models using in-memory SQLite.
"""
import uuid
import pytest
from app.models.provenance import ProvenanceRecord
from app.models.asset import WatermarkedAsset
from app.models.verification import VerificationRecord, VALID_VERDICTS


class TestProvenanceRecord:
    def test_insert_and_read(self, db_session):
        prov_uuid = uuid.uuid4()
        record = ProvenanceRecord(
            provenance_uuid=prov_uuid,
            source_type="ai_generated",
            generation_provider="openai",
            model_name="dall-e-3",
            prompt="a red sunset",
            metadata_json={"style": "photorealistic"},
        )
        db_session.add(record)
        db_session.commit()

        fetched = db_session.query(ProvenanceRecord).filter_by(provenance_uuid=prov_uuid).one()
        assert fetched.source_type == "ai_generated"
        assert fetched.model_name == "dall-e-3"
        assert fetched.metadata_json == {"style": "photorealistic"}
        assert fetched.created_at is not None

    def test_nullable_fields_are_optional(self, db_session):
        record = ProvenanceRecord(
            source_type="human_uploaded",
        )
        db_session.add(record)
        db_session.commit()
        fetched = db_session.query(ProvenanceRecord).filter_by(id=record.id).one()
        assert fetched.generation_provider is None
        assert fetched.prompt is None

    def test_provenance_uuid_unique(self, db_session):
        shared_uuid = uuid.uuid4()
        db_session.add(ProvenanceRecord(provenance_uuid=shared_uuid, source_type="ai_generated"))
        db_session.commit()

        db_session.add(ProvenanceRecord(provenance_uuid=shared_uuid, source_type="ai_generated"))
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
        db_session.rollback()


class TestWatermarkedAsset:
    def test_insert_with_foreign_key(self, db_session):
        prov = ProvenanceRecord(source_type="ai_generated")
        db_session.add(prov)
        db_session.commit()

        asset = WatermarkedAsset(
            provenance_record_id=prov.id,
            sha256="a" * 64,
            mime_type="image/png",
            width=512,
            height=512,
            watermark_delta=30.0,
        )
        db_session.add(asset)
        db_session.commit()

        fetched = db_session.query(WatermarkedAsset).filter_by(id=asset.id).one()
        assert fetched.sha256 == "a" * 64
        assert fetched.width == 512
        assert fetched.watermark_delta == 30.0
        assert fetched.provenance_record_id == prov.id


class TestVerificationRecord:
    def test_insert_valid_verdicts(self, db_session):
        for verdict in VALID_VERDICTS:
            v = VerificationRecord(
                submitted_sha256="b" * 64,
                verdict=verdict,
            )
            db_session.add(v)
        db_session.commit()
        count = db_session.query(VerificationRecord).filter_by(submitted_sha256="b" * 64).count()
        assert count == len(VALID_VERDICTS)

    def test_nullable_extracted_uuid(self, db_session):
        v = VerificationRecord(
            submitted_sha256="c" * 64,
            verdict="NO_WATERMARK_FOUND",
            extracted_provenance_uuid=None,
        )
        db_session.add(v)
        db_session.commit()
        fetched = db_session.query(VerificationRecord).filter_by(id=v.id).one()
        assert fetched.extracted_provenance_uuid is None
