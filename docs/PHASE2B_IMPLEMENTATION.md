# Phase 2B Implementation: Provenance Service Layer

---

## STEP 1 — Provenance Service Layer

### Status

| Item | Status |
|---|---|
| `app/services/provenance.py` — service functions | ✅ IMPLEMENTED |
| `dev_verify_provenance.py` — manual verification script | ✅ IMPLEMENTED |
| `tests/test_provenance_service.py` — automated tests | ✅ IMPLEMENTED |
| `app/services/image_validation.py` | ✅ IMPLEMENTED |
| `app/api/routes/upload.py` — `POST /upload/validate` | ✅ IMPLEMENTED |
| `dev_verify_upload.py` — manual verification script | ✅ IMPLEMENTED |
| `app/services/watermark.py` — embedding service | ✅ IMPLEMENTED |
| `dev_verify_watermark.py` — manual verification script | ✅ IMPLEMENTED |
| `tests/test_watermark_service.py` — automated tests | ✅ IMPLEMENTED |
| `app/services/asset.py` — asset registration service | ✅ IMPLEMENTED |
| `tests/test_asset_service.py` — automated tests | ✅ IMPLEMENTED |
| `app/api/routes/watermark.py` — `POST /watermark/embed` | ✅ IMPLEMENTED |
| `dev_verify_e2e.py` — manual verification script | ✅ IMPLEMENTED |
| `app/api/routes/verify.py` — `POST /verify` | ✅ IMPLEMENTED |
| `dev_verify_verification.py` — manual verification script | ✅ IMPLEMENTED |
| `tests/test_verify_route.py` — automated tests | ✅ IMPLEMENTED |

---

## What Was Implemented

### `backend/app/services/provenance.py`

Two functions were added. Neither one touches HTTP, images, or the watermark engine:

#### `create_provenance_record(db, data) → ProvenanceRecordRead`

1. Generates a fresh `uuid.uuid4()` for `provenance_uuid` (this is the UUID that will later be embedded in the watermark payload).
2. Constructs a `ProvenanceRecord` ORM object from the validated `ProvenanceRecordCreate` input.
3. Calls `db.add()` + `db.commit()` + `db.refresh()`.
4. On `SQLAlchemyError`: calls `db.rollback()` and raises `ProvenanceServiceError`.
5. Returns a `ProvenanceRecordRead` (Pydantic v2 schema) populated from the committed DB state.

#### `get_provenance_record_by_uuid(db, provenance_uuid) → ProvenanceRecordRead | None`

Queries by `provenance_uuid` (the watermark UUID, not the internal `id`). Returns `None` if not found.

**Fields used** — exactly the existing Phase 2A schema, no modifications:
- `id` (auto UUID)
- `provenance_uuid` (service-generated UUID)
- `source_type`
- `generation_provider`
- `model_name`
- `prompt`
- `metadata_json` → stored in the `metadata` column
- `created_at` (ORM default)

---

## Automated Test Results

```
22 passed, 6 warnings in 0.16s
```

Tests cover:
- Record creation with all fields
- Record creation with minimal fields (only `source_type`)
- UUID uniqueness: each call produces a distinct `provenance_uuid`
- Persistence: record exists in DB after service returns
- Return type is `ProvenanceRecordRead` (Pydantic schema)
- Duplicate `provenance_uuid` is rejected by the uniqueness constraint
- Lookup by `provenance_uuid` returns correct record
- Lookup of unknown UUID returns `None`
- All created fields match retrieved fields

---

## Manual Verification — Step 1

### Command

Run from the `backend/` directory with the venv active and PostgreSQL running:

```powershell
python dev_verify_provenance.py
```

### Expected Output

```
PROVENANCE CREATION TEST
----------------------------------------
  PASS  Database connection established

UUID generated:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Record id:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Created at:       2026-09-21 HH:MM:SS.ffffff+00:00
  PASS  Record inserted via service
  PASS  Record retrieved by provenance_uuid
  PASS  All fields verified

NEGATIVE TEST — duplicate provenance_uuid
  PASS  Duplicate provenance_uuid correctly rejected by PostgreSQL

CLEANUP
  PASS  Test record deleted and confirmed gone
----------------------------------------
ALL CHECKS PASSED

SQL QUERY TO INSPECT ANY PROVENANCE RECORD IN pgAdmin:
----------------------------------------

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
```

### What Each Step Proves

| Step | Proves |
|---|---|
| Database connection | `DATABASE_URL` in `.env` is correct and PostgreSQL is reachable |
| Record inserted | `create_provenance_record()` writes to PostgreSQL via SQLAlchemy |
| Record retrieved | `get_provenance_record_by_uuid()` can query by watermark UUID |
| Fields verified | All 6 user-supplied fields round-trip cleanly through DB |
| Negative test | `provenance_uuid` UNIQUE constraint is enforced at the PostgreSQL level |
| Cleanup | `DELETE` works and the row is truly gone |

---

## SQL Inspection Queries

Run these in **pgAdmin** or **psql** after the script completes (before cleanup, or insert your own row first):

```sql
-- View all provenance records
SELECT
    id,
    provenance_uuid,
    source_type,
    generation_provider,
    model_name,
    LEFT(prompt, 60) AS prompt_preview,
    metadata,
    created_at
FROM provenance_records
ORDER BY created_at DESC
LIMIT 10;

-- Count records
SELECT COUNT(*) FROM provenance_records;

-- Inspect the uniqueness constraint
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'provenance_records'::regclass;
```

---

## STEP 2 — Image Upload & Validation

### What Was Implemented

1. **`app/services/image_validation.py`**
   - Pure Python validation service independent of FastAPI.
   - Validates file size (≤ 20 MB).
   - Validates dimensions (64×64 to 8192×8192).
   - Verifies actual image decodability using Pillow (`Image.verify()`).
   - Validates formats: PNG, JPEG, WEBP, BMP, TIFF.
   - Validates color mode is convertible to RGB.

2. **`app/api/routes/upload.py`**
   - Provided `POST /upload/validate` endpoint.
   - Accepts multipart/form-data with a file.
   - Returns a structured JSON payload: `ImageValidationResponse`.
   - Never saves images to disk; purely an API layer for validation.

3. **`backend/requirements.txt`**
   - Added `python-multipart` to support `UploadFile` processing.

---

## STEP 3 — Watermark Engine Integration

### What Was Implemented

1. **`app/services/watermark.py`**
   - Pure Python bridge linking the Phase 0 watermarking engine with the backend's byte-level handling.
   - Takes validated raw image bytes and a UUID.
   - Decodes via `PIL.Image`, runs the existing `embed_watermark` function, and re-encodes as lossless PNG bytes.
   - Throws `WatermarkServiceError` on invalid payloads or process failures.

2. **Phase 0 Integrity Kept**
   - No modifications made to `watermark/embed.py`, `watermark/extract.py`, or any Phase 0–1.5 files.
   - The algorithm remains functionally identical, guaranteeing 100% compatibility with earlier tests.

3. **`tests/test_watermark_service.py`**
   - Automated tests that do a complete memory-only loop: embed a UUID via the backend service -> read the output PNG bytes -> extract the watermark using the Phase 0 extractor -> assert it matches the injected UUID.
   - Also tests garbage byte rejection and correct lossless PNG enforcement.

---

## STEP 4 — SHA-256 + Asset Registration

### What Was Implemented

1. **Permanent Import Solution (`setup.py`)**
   - Created a root-level `setup.py` and installed `multimedia-provenance` as an editable package into the `.venv`.
   - The backend no longer requires manual `PYTHONPATH` exports to import the `watermark` package. 

2. **`app/services/asset.py`**
   - Implemented `register_watermarked_asset` which accepts the final bytes.
   - Computes SHA-256 dynamically directly on the bytes.
   - Uses `PIL` to verify dimension properties on the exact bytes to be stored.
   - Inserts `WatermarkedAsset` with a strict foreign key link back to `ProvenanceRecord`.
   - Fixed a `MultipleResultsFound` issue by altering the SHA-256 retrieval query to use `.first()` rather than `.one_or_none()`, supporting multiple registrations of identical bytes.

3. **`backend/tests/conftest.py`**
   - Activated SQLite PRAGMA `foreign_keys=ON` by injecting an SQLAlchemy `@event.listens_for(engine, 'connect')` hook.
   - Now in-memory automated tests actually enforce DB foreign keys exactly like PostgreSQL.

4. **Tests and Verification**
   - Added automated tests spanning FK failure detection, SHA-256 correctness against binary data, and DB retrieval (`tests/test_asset_service.py`).
   - Created `dev_verify_asset.py` which demonstrates an end-to-end DB cycle enforcing cascade deletions and FK constraints.

---

## STEP 5 — End-to-End Workflow

### What Was Implemented

1. **`app/api/routes/watermark.py`**
   - Implemented the `POST /watermark/embed` endpoint.
   - Accepts standard `multipart/form-data` containing the image `file` and metadata (e.g., `source_type`, `generation_provider`).
   - Glues together all previous layers dynamically:
     1. Reads bytes and calls `validate_image_bytes`.
     2. Generates the `ProvenanceRecord` dynamically.
     3. Embeds the watermark payload deeply within the DWT-DCT coefficients.
     4. Saves the resulting lossless PNG bytes while simultaneously computing SHA-256 and populating `WatermarkedAsset`.
   - Returns the explicit raw PNG bytes directly to the client as an HTTP Response (`image/png`), placing the structural identifiers into custom headers (`X-Provenance-UUID`, `X-Asset-SHA256`).
   - Integrated safely into `main.py` routing.

2. **Tests and Verification**
   - Included robust exception handling for invalid file structures or database insertion constraints.
   - `test_watermark_route.py` runs full E2E HTTP simulations through the FastAPI `TestClient`, checking proper database reflection on correct insertion.
   - Fixed `TestClient` dependency threading model for UUID type mapping.
   - Created `dev_verify_e2e.py` which drives the whole process through live `httpx` connections to a running `uvicorn` instance, downloads the file dynamically, and triggers the standalone Phase 0 native `extract_watermark` function on the downloaded bits to guarantee they survive transit.

---

## STEP 6 — Watermark Verification Endpoint

### What Was Implemented

1. **`app/services/verification.py`**
   - Implemented the verification service layer bridging the Phase 0 native `extract_watermark_with_stats` logic with the FastAPI and Database layers.
   - Saves all extraction attempts into `verification_records`.
   - Explicitly cross-references successfully extracted watermarks with the `watermarked_assets` registry via `SHA-256`.
   - Dynamically downgrades `AUTHENTIC_UNMODIFIED` to `TRACED_BUT_MODIFIED` if the file hash has changed since leaving the platform, strictly enforcing provenance integrity tracking.

2. **`app/api/routes/verify.py`**
   - Implemented the `POST /verify` endpoint mapping an HTTP upload directly to the verification service.
   - If a valid payload is recovered, it fetches the corresponding `ProvenanceRecord` to surface origin data to the user.
   - Returns a structured `VerificationResponse` containing the `verdict`, `match_found` status, and `provenance_record`.

3. **Tests and Verification**
   - `test_verify_route.py` automates tests for `AUTHENTIC_UNMODIFIED`, `TRACED_BUT_MODIFIED` (using JPEG compression to simulate tampering), and `NO_WATERMARK_FOUND`.
   - `dev_verify_verification.py` runs a complete simulation dynamically using `httpx` and `uvicorn`, embedding a watermark via the Step 5 endpoint, heavily compressing it via Pillow, and feeding it to Step 6.

---

## NEXT PHASES

- Phase 3: AI image generation integration
- Phase 4: Frontend / React
- Phase 5: Authentication
