"""
backend/app/services/ai_providers/mock_provider.py

Mock AI generation provider for testing and development.
"""
import asyncio
import logging
from pathlib import Path
from typing import Tuple

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

class AIGenerationError(Exception):
    """Raised when AI generation fails."""
    pass

class MockAIProvider(BaseAIProvider):
    """
    Simulates AI image generation by loading a static image or generating a dummy one.
    """
    
    async def generate_image(self, prompt: str) -> Tuple[bytes, str, str]:
        logger.info(f"[MockProvider] Simulating image generation for prompt: {prompt!r}")
        
        # 1. Simulate network/generation delay
        await asyncio.sleep(1.0)
        
        # 2. Return the fallback synthetic image
        project_root = Path(__file__).parent.parent.parent.parent.parent
        fallback_path = project_root / "original_synthetic.png"
        
        if not fallback_path.exists():
            # Fallback to creating a dummy image dynamically if the file is missing
            try:
                from PIL import Image
                import io
                img = Image.new("RGB", (512, 512), color=(50, 150, 200))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue(), "local-mock", "pillow-dynamic-mock"
            except ImportError:
                raise AIGenerationError("Pillow is not installed and fallback image is missing.")
            
        try:
            with open(fallback_path, "rb") as f:
                image_bytes = f.read()
        except Exception as exc:
            raise AIGenerationError(f"Failed to load synthetic image: {exc}")
            
        return image_bytes, "stability-ai-mock", "stable-diffusion-v1-5-mock"
