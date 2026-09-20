"""
backend/dev_verify_ai_generation.py

DEVELOPMENT VERIFICATION SCRIPT — NOT PRODUCTION CODE.
Purpose: Manually verify Phase 3 Step 1 (AI Generation Service).

Prerequisites:
    Run this script from the backend/ directory with the venv active:
       python dev_verify_ai_generation.py

Expected output:
    AI GENERATION TEST
    ----------------------------------------
    [TEST] Generate Image from Prompt
      PASS  Called generate_image("A futuristic city at night")
      PASS  Received bytes (size > 0)
      PASS  Provider: stability-ai-mock
      PASS  Model: stable-diffusion-v1-5-mock
      PASS  Image is a valid decodable file (Format: PNG, Size: 512x512)
    ----------------------------------------
    ALL CHECKS PASSED
"""
import asyncio
import sys
import io
from PIL import Image
from app.services.ai_generation import generate_image, AIGenerationError

SEPARATOR = "-" * 40

def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(f"  PASS  {msg}")

async def main() -> None:
    print("\nAI GENERATION TEST")
    print(SEPARATOR)

    print("\n[TEST] Generate Image from Prompt")
    prompt = "A futuristic city at night"
    
    try:
        image_bytes, provider, model = await generate_image(prompt)
        ok(f'Called generate_image("{prompt}")')
    except AIGenerationError as exc:
        fail(f"AIGenerationError raised: {exc}")
    except Exception as exc:
        fail(f"Unexpected exception raised: {exc}")

    if not isinstance(image_bytes, bytes) or len(image_bytes) == 0:
        fail("Invalid or empty bytes returned.")
    ok(f"Received bytes (size: {len(image_bytes)} bytes)")

    if not provider:
        fail("Provider string is empty")
    ok(f"Provider: {provider}")
    
    if not model:
        fail("Model string is empty")
    ok(f"Model: {model}")

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        ok(f"Image is a valid decodable file (Format: {img.format}, Size: {img.width}x{img.height})")
    except Exception as exc:
        fail(f"Failed to decode returned image bytes: {exc}")
        
    print("\n" + SEPARATOR)
    print("ALL CHECKS PASSED\n")

if __name__ == "__main__":
    asyncio.run(main())
