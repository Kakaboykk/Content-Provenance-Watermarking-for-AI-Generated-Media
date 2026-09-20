"""
backend/dev_verify_watermark.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify that the backend's watermark integration service works.
         Creates a dummy image, generates a dummy UUID, embeds the watermark,
         saves the image to disk, loads it back, and extracts it independently.

Run from the backend/ directory with the venv active:
    python dev_verify_watermark.py

Expected output:
    WATERMARK INTEGRATION TEST
    ----------------------------------------
    [TEST] End-to-End Embed and Extract
      PASS  Generated dummy image
      PASS  Embedded UUID via service: <uuid>
      PASS  Saved watermarked image to dev_output_watermarked.png
      PASS  Independently extracted watermark from saved file
      PASS  Verdict: AUTHENTIC_UNMODIFIED
      PASS  Extracted UUID matches exactly!
"""
import io
import os
import sys
import uuid
from PIL import Image

# Ensure app package is importable when run from backend/
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.watermark import embed_watermark_in_bytes
from watermark.extract import extract_watermark

SEPARATOR = "-" * 40
TEST_FILE_NAME = "dev_output_watermarked.png"


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def main() -> None:
    print("\nWATERMARK INTEGRATION TEST")
    print(SEPARATOR)

    print("\n[TEST] End-to-End Embed and Extract")
    
    # 1. Create a dummy image
    img = Image.new("RGB", (512, 512), color=(100, 200, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    input_bytes = buf.getvalue()
    ok("Generated dummy image (JPEG bytes)")

    # 2. Generate target UUID
    target_uuid = uuid.uuid4()
    print(f"  Target UUID: {target_uuid}")

    # 3. Call backend service to embed
    try:
        watermarked_bytes = embed_watermark_in_bytes(input_bytes, target_uuid)
        ok(f"Embedded UUID via service (Output size: {len(watermarked_bytes)} bytes)")
    except Exception as exc:
        fail(f"Service failed to embed watermark: {exc}")

    # 4. Save to disk as a real PNG file to simulate what we'd do on S3/local storage
    try:
        with open(TEST_FILE_NAME, "wb") as f:
            f.write(watermarked_bytes)
        ok(f"Saved watermarked image to {TEST_FILE_NAME}")
    except Exception as exc:
        fail(f"Failed to save image to disk: {exc}")

    # 5. Independent Extraction Phase
    # Load from disk and call the Phase 0 extraction function
    try:
        loaded_img = Image.open(TEST_FILE_NAME)
        # Ensure we decode it
        loaded_img.load()
        ok("Loaded saved image from disk successfully")
    except Exception as exc:
        fail(f"Failed to load saved image from disk: {exc}")

    verdict, extracted_uuid = extract_watermark(loaded_img)
    print(f"  Verdict: {verdict}")
    print(f"  Extracted UUID: {extracted_uuid}")
    
    if verdict != "AUTHENTIC_UNMODIFIED":
        fail(f"Expected AUTHENTIC_UNMODIFIED, got {verdict}")
    ok("Verdict is correct")
    
    if extracted_uuid != target_uuid:
        fail(f"UUID mismatch! Expected {target_uuid}, got {extracted_uuid}")
    ok("Extracted UUID matches exactly!")

    # 6. Cleanup
    try:
        os.remove(TEST_FILE_NAME)
        ok(f"Cleaned up {TEST_FILE_NAME}")
    except OSError:
        pass

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
