"""
backend/app/services/ai_providers/base.py

Abstract base class for AI Image Generation providers.
"""
from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Abstract interface for AI image generation providers.
    """

    @abstractmethod
    async def generate_image(self, prompt: str) -> tuple[bytes, str, str]:
        """
        Generates an image from a text prompt.

        Args:
            prompt: The text prompt describing the desired image.

        Returns:
            A tuple containing:
            - image_bytes: The raw binary data of the generated image (PNG format).
            - provider_name: The name of the AI provider (e.g., "stability-ai", "huggingface").
            - model_name: The name of the model used (e.g., "stable-diffusion-xl").

        Raises:
            AIGenerationError: If generation fails for any reason (network, config, API error).
        """
        pass
