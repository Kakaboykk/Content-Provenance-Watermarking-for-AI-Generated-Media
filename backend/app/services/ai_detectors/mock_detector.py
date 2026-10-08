"""
backend/app/services/ai_detectors/mock_detector.py

Mock AI detector for automated tests and development without an API key.
"""
from .base import BaseAIDetector

class MockAIDetector(BaseAIDetector):
    """
    Returns deterministic results for automated tests.
    Does NOT perform actual AI analysis.
    """

    async def detect_image(self, image_bytes: bytes) -> dict:
        # For tests, we'll implement a simple heuristic based on the size or
        # mock content if needed, but returning a static AI_GENERATED is 
        # usually sufficient for basic integration.
        # To test multiple states, we can vary based on image size parity.
        size = len(image_bytes)
        
        # We can simulate different outputs based on file size modulo
        # 0 -> AI_GENERATED
        # 1 -> LIKELY_HUMAN
        # 2 -> UNCERTAIN
        state = size % 3
        
        if state == 0:
            label = "AI_GENERATED"
            confidence = 0.95
        elif state == 1:
            label = "LIKELY_HUMAN"
            confidence = 0.92
        else:
            label = "UNCERTAIN"
            confidence = 0.55

        return {
            "label": label,
            "confidence": confidence,
            "provider": "mock",
            "model": "mock-ai-detector"
        }
