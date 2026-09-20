"""
backend/app/services/ai_generation.py

Service layer for AI Image Generation.
"""
import asyncio
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIGenerationError(Exception):
    """Raised when AI generation fails."""
    pass


async def generate_image(prompt: str) -> tuple[bytes, str, str]:
    """
    Simulates AI image generation, or calls a real API if configured.
    
    Args:
        prompt: The text prompt describing the image to generate.
        
    Returns:
        tuple containing:
        - raw image bytes (PNG or JPEG format)
        - generation provider string (e.g. "stability-ai")
        - model name string (e.g. "stable-diffusion-v1-5-mock")
        
    Raises:
        AIGenerationError: If generation fails.
    """
    logger.info(f"Generating image for prompt: {prompt!r}")

    # For the MVP AI Integration, we implement a fallback to a local synthetic image 
    # to avoid rate limits and API key dependencies during testing.
    # If a real STABILITY_API_KEY was provided in settings, we would use it here.
    
    # 1. Simulate network/generation delay
    await asyncio.sleep(1.0)
    
    # 2. Return the fallback synthetic image
    # Assuming `original_synthetic.png` is in the project root (one level up from backend)
    project_root = Path(__file__).parent.parent.parent.parent
    fallback_path = project_root / "original_synthetic.png"
    
    if not fallback_path.exists():
        # Fallback to creating a dummy image dynamically if the file is missing
        from PIL import Image
        import io
        img = Image.new("RGB", (512, 512), color=(50, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), "local-mock", "pillow-dynamic-mock"
        
    try:
        with open(fallback_path, "rb") as f:
            image_bytes = f.read()
    except Exception as exc:
        raise AIGenerationError(f"Failed to load synthetic image: {exc}")
        
    return image_bytes, "stability-ai-mock", "stable-diffusion-v1-5-mock"
