"""
backend/app/services/ai_detectors/__init__.py

Provider factory for AI image detection.
"""
import logging
from .base import BaseAIDetector
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_ai_detector() -> BaseAIDetector:
    """
    Factory method to instantiate the correct AI detector based on configuration.
    """
    provider_name = settings.AI_DETECTOR_PROVIDER.lower()
    
    if provider_name == "mock":
        from .mock_detector import MockAIDetector
        return MockAIDetector()
        
    elif provider_name == "huggingface":
        from .huggingface_detector import HuggingFaceDetector
        return HuggingFaceDetector()
        
    elif provider_name == "sightengine":
        from .sightengine_detector import SightengineDetector
        return SightengineDetector()
        
    else:
        raise ValueError(f"Unknown AI_DETECTOR_PROVIDER configured: {provider_name}")
