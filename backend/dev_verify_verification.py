"""
backend/dev_verify_verification.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the full Verification Workflow (Phase 2B-6).

Prerequisites:
    1. The FastAPI server must be running locally:
       cd backend
       uvicorn app.main:app --reload
    
    2. Run this script from the backend/ directory with the venv active:
       python dev_verify_verification.py

Expected output:
    VERIFICATION WORKFLOW TEST
    ----------------------------------------
    [TEST] Unwatermarked Image Verification
      PASS  Generated unwatermarked image
      PASS  Endpoint returned 200 OK
      PASS  Verdict: NO_WATERMARK_FOUND
    
    [TEST] Authentic Watermarked Image Verification
      PASS  Called /watermark/embed to generate a genuine watermarked PNG
      PASS  Called /verify with the exact bytes
      PASS  Endpoint returned 200 OK
      PASS  Verdict: AUTHENTIC_UNMODIFIED
      PASS  Extracted UUID strictly matches Embedded UUID
    
    [TEST] Traced But Modified Verification
      PASS  Altered the watermarked PNG (JPEG compressed)
      PASS  Called /verify with the altered bytes
      PASS  Endpoint returned 200 OK
      PASS  Verdict: TRACED_BUT_MODIFIED
      PASS  Extracted UUID still successfully resolved back to original Provenance
"""
import io
import sys
import httpx
from PIL import Image

SEPARATOR = "-" * 40
BASE_URL = "http://127.0.0.1:8000"


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def main() -> None:
    print("\nVERIFICATION WORKFLOW TEST")
    print(SEPARATOR)

    try:
        r = httpx.get(f"{BASE_URL}/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at {BASE_URL}. Is uvicorn running?\nError: {exc}")

    # ---------------------------------------------------------
    # TEST 1: Unwatermarked
    # ---------------------------------------------------------
    print("\n[TEST] Unwatermarked Image Verification")
    img = Image.new("RGB", (512, 512), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    clean_bytes = buf.getvalue()
    ok("Generated unwatermarked image")

    files = {"file": ("clean.jpg", clean_bytes, "image/jpeg")}
    r = httpx.post(f"{BASE_URL}/verify", files=files, timeout=30.0)
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")
    
    data = r.json()
    if data.get("verdict") != "NO_WATERMARK_FOUND":
        fail(f"Expected NO_WATERMARK_FOUND, got {data.get('verdict')}")
    ok("Verdict: NO_WATERMARK_FOUND")

    # ---------------------------------------------------------
    # TEST 2: Authentic Watermarked Image
    # ---------------------------------------------------------
    print("\n[TEST] Authentic Watermarked Image Verification")
    # First embed an image
    embed_files = {"file": ("to_embed.jpg", clean_bytes, "image/jpeg")}
    embed_data = {"source_type": "scripted_test"}
    r_embed = httpx.post(f"{BASE_URL}/watermark/embed", files=embed_files, data=embed_data, timeout=30.0)
    if r_embed.status_code != 200:
        fail(f"Failed to embed watermark: {r_embed.text}")
    
    embedded_uuid = r_embed.headers.get("X-Provenance-UUID")
    watermarked_bytes = r_embed.content
    ok(f"Called /watermark/embed to generate a genuine watermarked PNG (UUID: {embedded_uuid})")

    # Now verify it
    verify_files = {"file": ("authentic.png", watermarked_bytes, "image/png")}
    r_verify = httpx.post(f"{BASE_URL}/verify", files=verify_files, timeout=30.0)
    if r_verify.status_code != 200:
        fail(f"Expected 200 OK, got {r_verify.status_code}. Response: {r_verify.text}")
    ok("Called /verify with the exact bytes and got 200 OK")
    
    data = r_verify.json()
    if data.get("verdict") != "AUTHENTIC_UNMODIFIED":
        fail(f"Expected AUTHENTIC_UNMODIFIED, got {data.get('verdict')}")
    ok("Verdict: AUTHENTIC_UNMODIFIED")
    
    if data.get("provenance_record")["provenance_uuid"] != embedded_uuid:
        fail("UUID mismatch!")
    ok("Extracted UUID strictly matches Embedded UUID")

    # ---------------------------------------------------------
    # TEST 3: Traced But Modified
    # ---------------------------------------------------------
    print("\n[TEST] Traced But Modified Verification")
    img_mod = Image.open(io.BytesIO(watermarked_bytes))
    buf_mod = io.BytesIO()
    # Save as high quality JPEG to simulate minor tampering/compression that the watermark survives
    img_mod.save(buf_mod, format="JPEG", quality=95)
    altered_bytes = buf_mod.getvalue()
    ok("Altered the watermarked PNG (JPEG compressed at Q95)")

    verify_mod_files = {"file": ("altered.jpg", altered_bytes, "image/jpeg")}
    r_verify_mod = httpx.post(f"{BASE_URL}/verify", files=verify_mod_files, timeout=30.0)
    if r_verify_mod.status_code != 200:
        fail(f"Expected 200 OK, got {r_verify_mod.status_code}")
    ok("Called /verify with the altered bytes and got 200 OK")

    data_mod = r_verify_mod.json()
    if data_mod.get("verdict") != "TRACED_BUT_MODIFIED":
        fail(f"Expected TRACED_BUT_MODIFIED, got {data_mod.get('verdict')}")
    ok("Verdict: TRACED_BUT_MODIFIED")
    
    if data_mod.get("provenance_record")["provenance_uuid"] != embedded_uuid:
        fail("UUID mismatch on traced image!")
    ok("Extracted UUID still successfully resolved back to original Provenance")

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
