"""
backend/dev_verify_generate_route.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the AI Generation API Endpoint (Phase 3 Step 2).

Prerequisites:
    1. The FastAPI server must be running locally:
       cd backend
       uvicorn app.main:app --reload
    
    2. Run this script from the backend/ directory with the venv active:
       python dev_verify_generate_route.py

Expected output:
    GENERATE ROUTE TEST
    ----------------------------------------
    [TEST] POST /generate Endpoint
      PASS  Called POST /generate with JSON payload {"prompt": "A futuristic city"}
      PASS  Endpoint returned 200 OK
      PASS  Received raw binary response (image/png)
      PASS  Headers correctly exposed X-AI-Provider (stability-ai-mock)
      PASS  Headers correctly exposed X-AI-Model (stable-diffusion-v1-5-mock)
      PASS  Image decoded successfully (Size: 512x512)
    ----------------------------------------
    ALL CHECKS PASSED
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
    print("\nGENERATE ROUTE TEST")
    print(SEPARATOR)

    try:
        r = httpx.get(f"{BASE_URL}/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at {BASE_URL}. Is uvicorn running?\nError: {exc}")

    # ---------------------------------------------------------
    # TEST 1: Generation Endpoint
    # ---------------------------------------------------------
    print("\n[TEST] POST /generate Endpoint")
    prompt_payload = {"prompt": "A futuristic city at night, 8k resolution"}
    
    r = httpx.post(f"{BASE_URL}/generate", json=prompt_payload, timeout=30.0)
    ok(f"Called POST /generate with JSON payload {prompt_payload}")
    
    if r.status_code != 200:
        fail(f"Expected 200 OK, got {r.status_code}. Response: {r.text}")
    ok("Endpoint returned 200 OK")
    
    content_type = r.headers.get("content-type", "")
    if "image/png" not in content_type:
        fail(f"Expected image/png, got {content_type}")
    ok("Received raw binary response (image/png)")
    
    provider = r.headers.get("X-AI-Provider")
    if not provider:
        fail("Missing X-AI-Provider header")
    ok(f"Headers correctly exposed X-AI-Provider ({provider})")
    
    model = r.headers.get("X-AI-Model")
    if not model:
        fail("Missing X-AI-Model header")
    ok(f"Headers correctly exposed X-AI-Model ({model})")
    
    # Try to decode the returned bytes
    try:
        img = Image.open(io.BytesIO(r.content))
        img.verify()
        # open again to check size since verify() resets
        img = Image.open(io.BytesIO(r.content))
        ok(f"Image decoded successfully (Size: {img.width}x{img.height})")
    except Exception as exc:
        fail(f"Failed to decode returned image: {exc}")

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
