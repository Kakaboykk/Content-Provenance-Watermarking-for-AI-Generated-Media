"""
backend/dev_verify_asset.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the asset registration service (Phase 2B-4)
         against a real PostgreSQL database.

Run from the backend/ directory with the venv active:

    python dev_verify_asset.py

Expected output:
    ASSET REGISTRATION TEST
    ----------------------------------------
    [TEST] Register Watermarked Asset
      PASS  Database connection established
      PASS  Created test ProvenanceRecord (id: <uuid>)
      PASS  Registered WatermarkedAsset (SHA-256: <hash>)
      PASS  Retrieved asset by SHA-256
      PASS  Asset properties matched input
    [TEST] Foreign Key Constraint
      PASS  PostgreSQL correctly rejected asset without valid provenance_id
    [TEST] Cleanup
      PASS  Test provenance and cascading asset deleted
"""
import hashlib
import sys
from pathlib import Path

# Ensure app package is importable when run from backend/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.core.database import SessionLocal, check_db_connection
from app.models.provenance import ProvenanceRecord
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.provenance import create_provenance_record
from app.services.asset import register_watermarked_asset, get_asset_by_sha256

SEPARATOR = "-" * 40

# 1x1 transparent PNG for testing
MINIMAL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15"
    b"\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x60\x00\x02\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def main() -> None:
    print("\nASSET REGISTRATION TEST")
    print(SEPARATOR)

    if not check_db_connection():
        fail("Cannot reach database. Is PostgreSQL running?")
    ok("Database connection established")

    db = SessionLocal()
    inserted_prov_id = None

    try:
        print("\n[TEST] Register Watermarked Asset")
        
        # 1. Create provenance record first (needed for FK)
        prov_data = ProvenanceRecordCreate(
            source_type="ai_generated",
            generation_provider="test_script"
        )
        prov = create_provenance_record(db, prov_data)
        inserted_prov_id = prov.id
        ok(f"Created test ProvenanceRecord (id: {prov.id})")

        # 2. Register asset
        expected_sha = hashlib.sha256(MINIMAL_PNG_BYTES).hexdigest()
        asset = register_watermarked_asset(
            db=db,
            provenance_record_id=prov.id,
            image_bytes=MINIMAL_PNG_BYTES,
            original_filename="minimal.png"
        )
        ok(f"Registered WatermarkedAsset (SHA-256: {asset.sha256})")

        # 3. Retrieve and verify
        fetched = get_asset_by_sha256(db, expected_sha)
        if not fetched:
            fail("Failed to retrieve asset by SHA-256")
        ok("Retrieved asset by SHA-256")

        assert fetched.sha256 == expected_sha, "SHA-256 mismatch"
        assert fetched.provenance_record_id == prov.id, "Provenance FK mismatch"
        assert fetched.width == 1 and fetched.height == 1, "Dimension mismatch"
        assert fetched.mime_type == "image/png", "MIME type mismatch"
        ok("Asset properties matched input")

        # 4. Foreign key enforcement test
        print("\n[TEST] Foreign Key Constraint")
        import uuid
        try:
            register_watermarked_asset(
                db=db,
                provenance_record_id=uuid.uuid4(),  # Does not exist
                image_bytes=MINIMAL_PNG_BYTES
            )
            fail("PostgreSQL allowed asset without a valid provenance_id!")
        except Exception as exc:
            db.rollback()
            ok("PostgreSQL correctly rejected asset without valid provenance_id")

        # 5. Cleanup
        print("\n[TEST] Cleanup")
        record_to_delete = (
            db.query(ProvenanceRecord)
            .filter(ProvenanceRecord.id == inserted_prov_id)
            .one_or_none()
        )
        if record_to_delete:
            db.delete(record_to_delete)
            db.commit()
            ok("Test provenance and cascading asset deleted")
        else:
            fail("Could not find test record for cleanup")

    except SystemExit:
        raise
    except Exception as exc:
        db.rollback()
        fail(f"Unexpected error: {exc}")
    finally:
        db.close()

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")
    
    print("SQL QUERY TO INSPECT ASSETS IN pgAdmin:")
    print(SEPARATOR)
    print("""
SELECT 
    w.id,
    w.sha256,
    w.original_filename,
    w.width,
    w.height,
    p.provenance_uuid
FROM watermarked_assets w
JOIN provenance_records p ON w.provenance_record_id = p.id
ORDER BY w.created_at DESC
LIMIT 10;
""")


if __name__ == "__main__":
    main()
