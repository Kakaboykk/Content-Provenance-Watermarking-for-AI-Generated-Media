"""
backend/dev_verify_e2e.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the full End-to-End Workflow (Phase 2B-5).

Prerequisites:
    1. The FastAPI server must be running locally:
       cd backend
       uvicorn app.main:app --reload
    
    2. Run this script from the backend/ directory with the venv active:
       python dev_verify_e2e.py

Expected output:
    END-TO-END WORKFLOW VERIFICATION
    ----------------------------------------
    [TEST] E2E Embed Endpoint (/watermark/embed)
      PASS  Generated valid dummy image
      PASS  Endpoint returned 200 OK
      PASS  Received X-Provenance-UUID header: <uuid>
      PASS  Received X-Asset-SHA256 header: <sha256>
      PASS  Saved output file to dev_e2e_output.png
      PASS  SHA-256 hash of saved file strictly matches header
      PASS  Independently extracted watermark UUID strictly matches header
"""
import hashlib
import io
import os
import sys
import httpx
from PIL import Image

# Ensure app package is importable when run from backend/
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from watermark.extract import extract_watermark

SEPARATOR = "-" * 40
API_URL = "http://127.0.0.1:8000/watermark/embed"
TEST_FILE_NAME = "dev_e2e_output.png"


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def main() -> None:
    print("\nEND-TO-END WORKFLOW VERIFICATION")
    print(SEPARATOR)

    try:
        r = httpx.get("http://127.0.0.1:8000/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at http://127.0.0.1:8000. Is uvicorn running?\nError: {exc}")

    print("\n[TEST] E2E Embed Endpoint (/watermark/embed)")
    
    # 1. Create a dummy image
    img = Image.new("RGB", (512, 512), color=(50, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    img_bytes = buf.getvalue()
    ok("Generated valid dummy image (512x512 JPEG)")

    # 2. Call API
    files = {"file": ("e2e_test.jpg", img_bytes, "image/jpeg")}
    data = {
        "source_type": "scripted_test",
        "generation_provider": "dev_verify_e2e"
    }
    
    # Use a higher timeout because watermark embedding takes CPU time
    try:
        r = httpx.post(API_URL, files=files, data=data, timeout=30.0)
    except httpx.ReadTimeout:
        fail("Endpoint timed out (likely busy embedding). Is the server running correctly?")
        
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")

    # 3. Check Headers
    prov_uuid = r.headers.get("X-Provenance-UUID")
    asset_sha = r.headers.get("X-Asset-SHA256")
    
    if not prov_uuid:
        fail("Missing X-Provenance-UUID header")
    ok(f"Received X-Provenance-UUID header: {prov_uuid}")
    
    if not asset_sha:
        fail("Missing X-Asset-SHA256 header")
    ok(f"Received X-Asset-SHA256 header: {asset_sha}")

    # 4. Save file
    try:
        with open(TEST_FILE_NAME, "wb") as f:
            f.write(r.content)
        ok(f"Saved output file to {TEST_FILE_NAME}")
    except OSError as exc:
        fail(f"Failed to save output file: {exc}")

    # 5. Verify SHA-256 natively
    actual_sha = hashlib.sha256(r.content).hexdigest()
    if actual_sha != asset_sha:
        fail(f"SHA-256 mismatch! Header: {asset_sha}, Actual: {actual_sha}")
    ok("SHA-256 hash of saved file strictly matches header")

    # 6. Verify Watermark natively
    try:
        loaded_img = Image.open(TEST_FILE_NAME)
        loaded_img.load()
        verdict, extracted_uuid = extract_watermark(loaded_img)
        if verdict != "AUTHENTIC_UNMODIFIED":
            fail(f"Extraction failed with verdict: {verdict}")
        if str(extracted_uuid) != prov_uuid:
            fail(f"UUID mismatch! Header: {prov_uuid}, Extracted: {extracted_uuid}")
        ok("Independently extracted watermark UUID strictly matches header")
    except Exception as exc:
        fail(f"Failed to independently extract watermark: {exc}")

    # 7. Cleanup
    try:
        os.remove(TEST_FILE_NAME)
        ok(f"Cleaned up {TEST_FILE_NAME}")
    except OSError:
        pass

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")
    print("Check your PostgreSQL database to see the newly created provenance and asset records!\n")

if __name__ == "__main__":
    main()
