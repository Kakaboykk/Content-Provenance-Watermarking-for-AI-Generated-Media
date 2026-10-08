"""
backend/app/services/ai_providers/__init__.py

Provider Factory for AI Image Generation.
"""
from app.core.config import settings
from .base import BaseAIProvider
from .mock_provider import MockAIProvider, AIGenerationError
from .huggingface_provider import HuggingFaceProvider
from .stability_provider import StabilityProvider


def get_ai_provider() -> BaseAIProvider:
    """
    Factory function that returns the configured AI provider instance.
    
    Returns:
        An instance of a class extending BaseAIProvider.
        
    Raises:
        ValueError: If the configured provider is unknown or invalid.
    """
    provider_name = settings.AI_PROVIDER.lower().strip()
    
    if provider_name == "mock":
        return MockAIProvider()
    elif provider_name == "huggingface":
        return HuggingFaceProvider()
    elif provider_name == "stability":
        return StabilityProvider()
    else:
        raise ValueError(f"Unknown AI_PROVIDER configured: '{provider_name}'. Expected 'mock', 'huggingface', or 'stability'.")
