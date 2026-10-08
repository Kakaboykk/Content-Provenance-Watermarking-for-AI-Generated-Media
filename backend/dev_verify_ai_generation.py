"""
backend/dev_verify_ai_generation.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify the AI Generation Endpoint (Phase 5A).
"""
import sys
import httpx
from app.core.config import settings

BASE_URL = "http://127.0.0.1:8000"
SEPARATOR = "-" * 40

def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(f"  PASS  {msg}")

def test_generation():
    print(f"\n[TEST] {settings.AI_PROVIDER.upper()} AI Generation")
    
    prompt = "A futuristic city at night with neon lights"
    r = httpx.post(f"{BASE_URL}/generate", json={"prompt": prompt}, timeout=60.0)
    
    if r.status_code != 200:
        fail(f"POST /generate returned {r.status_code}. Details: {r.text}")
    ok("POST /generate returned 200")
    
    content_type = r.headers.get("Content-Type")
    if content_type != "image/png":
        fail(f"Expected image/png, got {content_type}")
    ok("Response Content-Type is image/png")
    
    image_bytes = r.content
    if not image_bytes:
        fail("Received empty image bytes")
    ok("Binary image received")
    
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        ok("Image successfully decoded")
        ok(f"Image dimensions are valid: {img.size}")
    except Exception as exc:
        fail(f"Failed to decode image: {exc}")
        
    provider = r.headers.get("X-AI-Provider")
    model = r.headers.get("X-AI-Model")
    
    if not provider:
        fail("X-AI-Provider header is missing")
    ok(f"X-AI-Provider is present: {provider}")
    
    if not model:
        fail("X-AI-Model header is missing")
    ok(f"X-AI-Model is present: {model}")
    
    # Provider-specific checks
    if settings.AI_PROVIDER == "mock":
        if provider not in ("stability-ai-mock", "local-mock"):
            fail(f"Expected mock provider, got {provider}")
    elif settings.AI_PROVIDER == "huggingface":
        if provider != "huggingface":
            fail(f"Expected huggingface, got {provider}")
        if model != settings.AI_MODEL:
            fail(f"Expected model {settings.AI_MODEL}, got {model}")
    
    ok("Provider and Model headers match configuration")

def main():
    print("\nAI GENERATION WORKFLOW TEST")
    print(SEPARATOR)
    
    try:
        r = httpx.get(f"{BASE_URL}/health")
        r.raise_for_status()
    except Exception as exc:
        fail(f"Could not reach server at {BASE_URL}. Is uvicorn running?\nError: {exc}")

    test_generation()
    
    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")

if __name__ == "__main__":
    main()
