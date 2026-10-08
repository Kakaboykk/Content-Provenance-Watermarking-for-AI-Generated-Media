"""
backend/app/services/ai_detectors/base.py

Abstract base class for AI image detection providers.
"""
from abc import ABC, abstractmethod


class BaseAIDetector(ABC):
    """
    Interface for AI-generated image detection.
    """

    @abstractmethod
    async def detect_image(self, image_bytes: bytes) -> dict:
        """
        Analyze an image and return a probabilistic detection result.

        Args:
            image_bytes (bytes): The raw image file bytes.

        Returns:
            dict: The normalized detection result.
            Expected format:
            {
                "label": "AI_GENERATED" | "LIKELY_HUMAN" | "UNCERTAIN",
                "confidence": float (0.0 to 1.0),
                "provider": str,
                "model": str
            }
        """
        pass
