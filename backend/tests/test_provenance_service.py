"""
backend/tests/test_provenance_service.py

Automated tests for the provenance service layer.
Uses the in-memory SQLite fixture from conftest.py — no PostgreSQL needed.
"""
import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.provenance import ProvenanceRecord
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.provenance import (
    ProvenanceServiceError,
    create_provenance_record,
    get_provenance_record_by_uuid,
)


class TestCreateProvenanceRecord:
    """Tests for create_provenance_record()."""

    def test_creates_record_with_all_fields(self, db_session):
        data = ProvenanceRecordCreate(
            source_type="ai_generated",
            generation_provider="openai",
            model_name="dall-e-3",
            prompt="a red sunset",
            metadata_json={"style": "photorealistic", "seed": 42},
        )
        result = create_provenance_record(db_session, data)

        assert result.id is not None
        assert result.provenance_uuid is not None
        assert result.source_type == "ai_generated"
        assert result.generation_provider == "openai"
        assert result.model_name == "dall-e-3"
        assert result.prompt == "a red sunset"
        assert result.metadata_json == {"style": "photorealistic", "seed": 42}
        assert result.created_at is not None

    def test_creates_record_with_minimal_fields(self, db_session):
        """Only source_type is required; all others may be None."""
        data = ProvenanceRecordCreate(source_type="human_uploaded")
        result = create_provenance_record(db_session, data)

        assert result.source_type == "human_uploaded"
        assert result.generation_provider is None
        assert result.model_name is None
        assert result.prompt is None
        assert result.metadata_json is None

    def test_generated_uuid_is_unique_per_call(self, db_session):
        """Each call must produce a distinct provenance_uuid."""
        data = ProvenanceRecordCreate(source_type="ai_generated")
        r1 = create_provenance_record(db_session, data)
        r2 = create_provenance_record(db_session, data)

        assert r1.provenance_uuid != r2.provenance_uuid
        assert r1.id != r2.id

    def test_record_is_actually_persisted(self, db_session):
        """Verify the record exists in the DB after the service returns."""
        data = ProvenanceRecordCreate(source_type="ai_generated")
        result = create_provenance_record(db_session, data)

        # Query directly via ORM — bypassing the service
        raw = (
            db_session.query(ProvenanceRecord)
            .filter_by(id=result.id)
            .one_or_none()
        )
        assert raw is not None
        assert raw.provenance_uuid == result.provenance_uuid

    def test_returns_provenance_record_read_schema(self, db_session):
        """Return value must be a ProvenanceRecordRead instance."""
        from app.schemas.provenance import ProvenanceRecordRead
        data = ProvenanceRecordCreate(source_type="ai_generated")
        result = create_provenance_record(db_session, data)
        assert isinstance(result, ProvenanceRecordRead)

    def test_duplicate_provenance_uuid_raises_service_error(self, db_session):
        """
        Manually forcing a duplicate provenance_uuid must be rejected.
        The service itself generates UUIDs, so duplicates can only occur
        if someone inserts directly via ORM (or astronomically rare collision).
        We test by inserting a raw record and then checking that the DB
        rejects a second one with the same provenance_uuid.
        """
        shared_uuid = uuid.uuid4()
        db_session.add(ProvenanceRecord(
            provenance_uuid=shared_uuid,
            source_type="ai_generated",
        ))
        db_session.commit()

        db_session.add(ProvenanceRecord(
            provenance_uuid=shared_uuid,
            source_type="ai_generated",
        ))
        with pytest.raises(Exception):   # IntegrityError (unique constraint)
            db_session.commit()
        db_session.rollback()


class TestGetProvenanceRecordByUuid:
    """Tests for get_provenance_record_by_uuid()."""

    def test_returns_existing_record(self, db_session):
        data = ProvenanceRecordCreate(source_type="ai_generated", model_name="sdxl")
        created = create_provenance_record(db_session, data)

        fetched = get_provenance_record_by_uuid(db_session, created.provenance_uuid)
        assert fetched is not None
        assert fetched.provenance_uuid == created.provenance_uuid
        assert fetched.model_name == "sdxl"

    def test_returns_none_for_unknown_uuid(self, db_session):
        result = get_provenance_record_by_uuid(db_session, uuid.uuid4())
        assert result is None

    def test_retrieved_fields_match_created_fields(self, db_session):
        data = ProvenanceRecordCreate(
            source_type="ai_generated",
            generation_provider="stability-ai",
            model_name="stable-diffusion-xl",
            prompt="a blue mountain",
            metadata_json={"cfg_scale": 7},
        )
        created = create_provenance_record(db_session, data)
        fetched = get_provenance_record_by_uuid(db_session, created.provenance_uuid)

        assert fetched.source_type == created.source_type
        assert fetched.generation_provider == created.generation_provider
        assert fetched.model_name == created.model_name
        assert fetched.prompt == created.prompt
        assert fetched.metadata_json == created.metadata_json
        assert fetched.created_at == created.created_at
