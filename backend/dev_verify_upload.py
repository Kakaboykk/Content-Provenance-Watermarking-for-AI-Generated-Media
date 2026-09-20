"""
backend/dev_verify_upload.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify that the POST /upload/validate endpoint correctly
         handles image uploads.

Prerequisites:
    1. The FastAPI server must be running locally:
       cd backend
       uvicorn app.main:app --reload
    
    2. Run this script from the backend/ directory with the venv active:
       python dev_verify_upload.py

Expected output:
    IMAGE UPLOAD VALIDATION TEST
    ----------------------------------------
    [TEST 1] Valid PNG image
      PASS  Endpoint returned 200 OK
      PASS  Response valid=True
    [TEST 2] Invalid image (text file)
      PASS  Endpoint returned 200 OK
      PASS  Response valid=False
      PASS  Correct error: The uploaded file could not be identified...
    [TEST 3] Too small image
      PASS  Endpoint returned 200 OK
      PASS  Response valid=False
      PASS  Correct error: dimensions ... are below the minimum...
"""
import io
import sys
import httpx
from PIL import Image

SEPARATOR = "-" * 40
API_URL = "http://127.0.0.1:8000/upload/validate"


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def make_png(width: int, height: int) -> bytes:
    img = Image.new("RGB", (width, height), color=(50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    print("\nIMAGE UPLOAD VALIDATION TEST")
    print(SEPARATOR)

    try:
        # Ping the health endpoint first to ensure server is running
        r = httpx.get("http://127.0.0.1:8000/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at http://127.0.0.1:8000. Is uvicorn running?\nError: {exc}")

    # ── TEST 1: Valid PNG ────────────────────────────────────────────────
    print("\n[TEST 1] Valid PNG image (512x512)")
    valid_data = make_png(512, 512)
    files = {"file": ("test.png", valid_data, "image/png")}
    
    r = httpx.post(API_URL, files=files)
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")
    
    data = r.json()
    if data.get("valid") is not True:
        fail(f"Expected valid=True, got {data}")
    ok("Response valid=True")
    print(f"  Info: Format={data.get('detected_format')}, Size={data.get('width')}x{data.get('height')}")

    # ── TEST 2: Invalid text file ─────────────────────────────────────────
    print("\n[TEST 2] Invalid image (text file)")
    invalid_data = b"This is not a real image."
    files = {"file": ("fake.jpg", invalid_data, "image/jpeg")}
    
    r = httpx.post(API_URL, files=files)
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")
    
    data = r.json()
    if data.get("valid") is not False:
        fail(f"Expected valid=False, got {data}")
    ok("Response valid=False")
    
    errors = data.get("errors", [])
    if not any("could not be identified" in str(e).lower() for e in errors):
        fail(f"Expected unidentifiable image error, got: {errors}")
    ok(f"Correct error received: {errors[0]}")

    # ── TEST 3: Too small image ───────────────────────────────────────────
    print("\n[TEST 3] Too small image (32x32)")
    small_data = make_png(32, 32)
    files = {"file": ("small.png", small_data, "image/png")}
    
    r = httpx.post(API_URL, files=files)
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")
    
    data = r.json()
    if data.get("valid") is not False:
        fail(f"Expected valid=False, got {data}")
    ok("Response valid=False")
    
    errors = data.get("errors", [])
    if not any("minimum" in str(e).lower() for e in errors):
        fail(f"Expected minimum dimension error, got: {errors}")
    ok(f"Correct error received: {errors[0]}")

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
