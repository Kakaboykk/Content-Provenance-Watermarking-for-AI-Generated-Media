"""
backend/dev_verify_ai_e2e.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the AI End-to-End Workflow (Phase 3 Step 3).

Prerequisites:
    1. The FastAPI server must be running locally:
       cd backend
       uvicorn app.main:app --reload
    
    2. Run this script from the backend/ directory with the venv active:
       python dev_verify_ai_e2e.py

Expected output:
    AI END-TO-END WORKFLOW TEST
    ----------------------------------------
    [STEP 1] Generating AI Image
      PASS  Called POST /generate
      PASS  Captured metadata: Provider=stability-ai-mock, Model=stable-diffusion-v1-5-mock

    [STEP 2] Embedding Watermark & Registering Provenance
      PASS  Called POST /watermark/embed with AI bytes + AI metadata
      PASS  Received watermarked PNG
      PASS  Captured X-Provenance-UUID and X-Asset-SHA256 headers

    [STEP 3] Verifying Final Asset
      PASS  Called POST /verify with the watermarked PNG
      PASS  Verdict: AUTHENTIC_UNMODIFIED
      PASS  Provenance exactly matches the originally generated AI metadata
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
    print("\nAI END-TO-END WORKFLOW TEST")
    print(SEPARATOR)

    try:
        r = httpx.get(f"{BASE_URL}/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at {BASE_URL}. Is uvicorn running?\nError: {exc}")

    # ---------------------------------------------------------
    # STEP 1: Generate AI Image
    # ---------------------------------------------------------
    print("\n[STEP 1] Generating AI Image")
    prompt = "A majestic cyberpunk cityscape at sunset"
    r_gen = httpx.post(f"{BASE_URL}/generate", json={"prompt": prompt}, timeout=30.0)
    if r_gen.status_code != 200:
        fail(f"Generation failed. Expected 200 OK, got {r_gen.status_code}")
    ok("Called POST /generate")
    
    provider = r_gen.headers.get("X-AI-Provider")
    model = r_gen.headers.get("X-AI-Model")
    raw_bytes = r_gen.content
    ok(f"Captured metadata: Provider={provider}, Model={model}")

    # ---------------------------------------------------------
    # STEP 2: Embed Watermark & Register Provenance
    # ---------------------------------------------------------
    print("\n[STEP 2] Embedding Watermark & Registering Provenance")
    embed_data = {
        "source_type": "ai_generated",
        "generation_provider": provider,
        "model_name": model,
        "prompt": prompt,
    }
    embed_files = {
        "file": ("ai_generated.png", raw_bytes, "image/png")
    }
    r_embed = httpx.post(f"{BASE_URL}/watermark/embed", data=embed_data, files=embed_files, timeout=30.0)
    
    if r_embed.status_code != 200:
        fail(f"Embedding failed. Expected 200 OK, got {r_embed.status_code}. Details: {r_embed.text}")
    ok("Called POST /watermark/embed with AI bytes + AI metadata")
    
    watermarked_bytes = r_embed.content
    prov_uuid = r_embed.headers.get("X-Provenance-UUID")
    ok(f"Received watermarked PNG (UUID: {prov_uuid})")

    # ---------------------------------------------------------
    # STEP 3: Verify Final Asset
    # ---------------------------------------------------------
    print("\n[STEP 3] Verifying Final Asset")
    verify_files = {
        "file": ("protected_image.png", watermarked_bytes, "image/png")
    }
    r_verify = httpx.post(f"{BASE_URL}/verify", files=verify_files, timeout=30.0)
    
    if r_verify.status_code != 200:
        fail(f"Verification failed. Expected 200 OK, got {r_verify.status_code}")
    ok("Called POST /verify with the watermarked PNG")
    
    data = r_verify.json()
    if data.get("verdict") != "AUTHENTIC_UNMODIFIED":
        fail(f"Expected AUTHENTIC_UNMODIFIED, got {data.get('verdict')}")
    ok("Verdict: AUTHENTIC_UNMODIFIED")
    
    prov_record = data.get("provenance_record", {})
    if prov_record.get("generation_provider") != provider or prov_record.get("model_name") != model:
        fail("Provenance metadata did not survive the E2E loop correctly.")
    ok("Provenance exactly matches the originally generated AI metadata")

    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")


if __name__ == "__main__":
    main()
