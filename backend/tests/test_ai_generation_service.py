"""
backend/tests/test_ai_generation_service.py

Tests for Phase 3 Step 1: AI Generation Service.
"""
import pytest
from app.services.ai_generation import generate_image, AIGenerationError

@pytest.mark.asyncio
async def test_generate_image_success():
    prompt = "A futuristic city at night"
    
    # 1. Call the service
    image_bytes, provider, model = await generate_image(prompt)
    
    # 2. Verify outputs
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    assert provider in ("stability-ai-mock", "local-mock")
    assert model in ("stable-diffusion-v1-5-mock", "pillow-dynamic-mock")

    # 3. Verify it's a valid image
    import io
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        assert img.size[0] >= 512
        assert img.size[1] >= 512
    except Exception as exc:
        pytest.fail(f"Returned bytes are not a valid image: {exc}")
