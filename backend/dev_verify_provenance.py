"""
backend/dev_verify_provenance.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify that the provenance service layer works end-to-end
         against a real PostgreSQL database.

Run from the backend/ directory with the venv active:

    python dev_verify_provenance.py

Expected output:
    PROVENANCE CREATION TEST
    ------------------------
    UUID generated:   <uuid>
    Record inserted:  PASS
    Record retrieved: PASS
    Fields verified:  PASS
    Record cleanup:   PASS
    Negative test:    PASS (invalid verdict rejected)
"""
import sys
import uuid
from pathlib import Path

# Ensure app package is importable when run from backend/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from sqlalchemy import text
from app.core.database import SessionLocal, check_db_connection
from app.models.provenance import ProvenanceRecord
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.provenance import create_provenance_record, get_provenance_record_by_uuid

SEPARATOR = "-" * 40


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def main() -> None:
    print("\nPROVENANCE CREATION TEST")
    print(SEPARATOR)

    # ── 0. Database connectivity ────────────────────────────────────────────
    if not check_db_connection():
        fail("Cannot reach database. Is PostgreSQL running and DATABASE_URL correct?")
    ok("Database connection established")

    db = SessionLocal()
    inserted_id = None

    try:
        # ── 1. Create a provenance record via the service ───────────────────
        input_data = ProvenanceRecordCreate(
            source_type="ai_generated",
            generation_provider="test-provider",
            model_name="test-model-v1",
            prompt="A vivid red sunset over the ocean (Phase 2B Step 1 test)",
            metadata_json={"phase": "2B", "step": 1, "test": True},
        )

        result = create_provenance_record(db, input_data)
        inserted_id = result.id

        print(f"\nUUID generated:   {result.provenance_uuid}")
        print(f"Record id:        {result.id}")
        print(f"Created at:       {result.created_at}")
        ok("Record inserted via service")

        # ── 2. Read it back using the service lookup function ───────────────
        fetched = get_provenance_record_by_uuid(db, result.provenance_uuid)
        if fetched is None:
            fail("get_provenance_record_by_uuid returned None — record not found")
        ok("Record retrieved by provenance_uuid")

        # ── 3. Verify individual fields ─────────────────────────────────────
        assert fetched.source_type == "ai_generated",  \
            f"source_type mismatch: {fetched.source_type!r}"
        assert fetched.generation_provider == "test-provider", \
            f"generation_provider mismatch: {fetched.generation_provider!r}"
        assert fetched.model_name == "test-model-v1", \
            f"model_name mismatch: {fetched.model_name!r}"
        assert fetched.prompt is not None and "sunset" in fetched.prompt, \
            f"prompt mismatch: {fetched.prompt!r}"
        assert fetched.metadata_json == {"phase": "2B", "step": 1, "test": True}, \
            f"metadata_json mismatch: {fetched.metadata_json!r}"
        assert fetched.provenance_uuid == result.provenance_uuid, \
            "provenance_uuid changed after retrieval"
        assert fetched.created_at is not None, "created_at is None"
        ok("All fields verified")

        # ── 4. Confirm uniqueness constraint blocks duplicate provenance_uuid
        print("\nNEGATIVE TEST — duplicate provenance_uuid")
        dup = ProvenanceRecord(
            provenance_uuid=result.provenance_uuid,   # intentional duplicate
            source_type="ai_generated",
        )
        db.add(dup)
        try:
            db.commit()
            fail("Duplicate provenance_uuid was accepted — uniqueness constraint broken")
        except Exception:
            db.rollback()
            ok("Duplicate provenance_uuid correctly rejected by PostgreSQL")

        # ── 5. Cleanup — delete ONLY the test record ────────────────────────
        print("\nCLEANUP")
        record_to_delete = (
            db.query(ProvenanceRecord)
            .filter(ProvenanceRecord.id == inserted_id)
            .one_or_none()
        )
        if record_to_delete is None:
            fail("Could not find record for cleanup")

        db.delete(record_to_delete)
        db.commit()

        # Confirm deletion
        gone = (
            db.query(ProvenanceRecord)
            .filter(ProvenanceRecord.id == inserted_id)
            .one_or_none()
        )
        if gone is not None:
            fail("Record still exists after deletion")
        ok("Test record deleted and confirmed gone")

    except SystemExit:
        raise
    except Exception as exc:
        db.rollback()
        print(f"  FAIL  Unexpected error: {exc}")
        raise
    finally:
        db.close()

    print(SEPARATOR)
    print("ALL CHECKS PASSED\n")

    # ── SQL you can run in pgAdmin for an independent look ──────────────────
    print("SQL QUERY TO INSPECT ANY PROVENANCE RECORD IN pgAdmin:")
    print(SEPARATOR)
    print("""
SELECT
    id,
    provenance_uuid,
    source_type,
    generation_provider,
    model_name,
    LEFT(prompt, 60)  AS prompt_preview,
    metadata,
    created_at
FROM provenance_records
ORDER BY created_at DESC
LIMIT 10;
""")


if __name__ == "__main__":
    main()
