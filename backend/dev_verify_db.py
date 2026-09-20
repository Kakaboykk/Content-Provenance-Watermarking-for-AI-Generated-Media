"""
backend/dev_verify_db.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.

Purpose: Manually verify that SQLAlchemy can communicate with PostgreSQL
and that the schema is correct.

Run from the backend/ directory:
    python dev_verify_db.py

Expected output:
    [OK] Database connection established
    [OK] Inserted ProvenanceRecord: <uuid>
    [OK] Read back record: source_type='ai_generated'  provenance_uuid=<uuid>
    [OK] Verification complete. Cleaning up...
    [OK] Done.
"""
import sys
import uuid
from pathlib import Path

# Ensure app is importable when run from backend/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.core.database import SessionLocal, check_db_connection
from app.models.provenance import ProvenanceRecord


def main() -> None:
    # 1. Connection check
    if not check_db_connection():
        print("[FAIL] Cannot connect to database. Check DATABASE_URL in .env")
        sys.exit(1)
    print("[OK] Database connection established")

    db = SessionLocal()
    test_record = None
    try:
        # 2. Insert a test record
        test_uuid = uuid.uuid4()
        test_record = ProvenanceRecord(
            provenance_uuid=test_uuid,
            source_type="ai_generated",
            generation_provider="test-provider",
            model_name="test-model-v1",
            prompt="A test image for Phase 2A verification",
            metadata_json={"phase": "2A", "test": True},
        )
        db.add(test_record)
        db.commit()
        db.refresh(test_record)

        print(f"[OK] Inserted ProvenanceRecord: id={test_record.id}")

        # 3. Read it back
        fetched = (
            db.query(ProvenanceRecord)
            .filter_by(provenance_uuid=test_uuid)
            .one()
        )
        print(
            f"[OK] Read back record: "
            f"source_type={fetched.source_type!r}  "
            f"provenance_uuid={fetched.provenance_uuid}"
        )
        assert fetched.source_type == "ai_generated"
        assert fetched.provenance_uuid == test_uuid

        print("[OK] Verification complete. Cleaning up...")
        db.delete(fetched)
        db.commit()
        print("[OK] Done.")

    except Exception as exc:
        db.rollback()
        print(f"[FAIL] {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
