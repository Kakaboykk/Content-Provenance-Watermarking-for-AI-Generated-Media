"""
backend/app/services/ai_generation.py

Service layer for AI Image Generation.
"""
import logging
from app.services.ai_providers import get_ai_provider, AIGenerationError

logger = logging.getLogger(__name__)

async def generate_image(prompt: str) -> tuple[bytes, str, str]:
    """
    Generates an image from a text prompt using the configured AI Provider.
    
    Args:
        prompt: The text prompt describing the image to generate.
        
    Returns:
        tuple containing:
        - raw image bytes (PNG format)
        - generation provider string (e.g. "stability-ai-mock" or "huggingface")
        - model name string (e.g. "stable-diffusion-v1-5-mock")
        
    Raises:
        AIGenerationError: If generation fails due to network, config, or API error.
    """
    logger.info(f"Generating image for prompt: {prompt!r}")

    try:
        provider = get_ai_provider()
    except ValueError as e:
        logger.error(f"Configuration error getting AI provider: {e}")
        # Reraise as AIGenerationError to keep API exceptions consistent
        raise AIGenerationError(str(e))
        
    return await provider.generate_image(prompt)
