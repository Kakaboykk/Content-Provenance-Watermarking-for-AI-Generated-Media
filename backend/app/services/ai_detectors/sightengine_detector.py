"""
backend/app/services/ai_detectors/sightengine_detector.py

Real AI image detection provider using Sightengine.
"""
import logging
from typing import Dict

import httpx

from .base import BaseAIDetector
from app.core.config import settings

logger = logging.getLogger(__name__)

class SightengineDetector(BaseAIDetector):
    """
    Calls the Sightengine AI detection API.
    """

    def __init__(self):
        if not settings.SIGHTENGINE_API_USER or not settings.SIGHTENGINE_API_SECRET:
            raise ValueError("SIGHTENGINE_API_USER or SIGHTENGINE_API_SECRET is not configured.")
            
        self.api_user = settings.SIGHTENGINE_API_USER
        self.api_secret = settings.SIGHTENGINE_API_SECRET
        self.threshold = settings.AI_DETECTOR_THRESHOLD
        self.base_url = "https://api.sightengine.com/1.0/check.json"

    async def detect_image(self, image_bytes: bytes) -> Dict:
        logger.info("[SightengineDetector] Analyzing image.")
        
        data = {
            'models': 'genai',
            'api_user': self.api_user,
            'api_secret': self.api_secret
        }
        
        files = {
            'media': ('image.jpg', image_bytes, 'application/octet-stream')
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    data=data,
                    files=files
                )
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        raise ValueError("Sightengine returned malformed JSON.")
                        
                    if result.get("status") != "success":
                        err_msg = result.get("error", {}).get("message", "Unknown API error")
                        raise ValueError(f"Sightengine API Error: {err_msg}")
                        
                    type_data = result.get("type", {})
                    if "ai_generated" not in type_data:
                        raise ValueError("Missing 'ai_generated' field in response.")
                        
                    ai_score = type_data["ai_generated"]
                    human_score = type_data.get("human", 1.0 - ai_score)
                    
                    if ai_score >= self.threshold:
                        label = "AI_GENERATED"
                        confidence = ai_score
                    elif human_score >= self.threshold:
                        label = "LIKELY_HUMAN"
                        confidence = human_score
                    else:
                        label = "UNCERTAIN"
                        confidence = max(ai_score, human_score)
                        
                    return {
                        "label": label,
                        "confidence": confidence,
                        "provider": "sightengine",
                        "model": "genai"
                    }
                    
                elif response.status_code == 401:
                    raise PermissionError("Sightengine authentication failed. Please check credentials.")
                elif response.status_code == 402:
                    raise PermissionError("Insufficient credits for Sightengine Provider.")
                elif response.status_code == 429:
                    raise ConnectionError("Sightengine rate limit exceeded. Please try again later.")
                elif response.status_code >= 500:
                    raise ConnectionError(f"Sightengine internal error: HTTP {response.status_code}")
                else:
                    raise ConnectionError(f"Sightengine returned an error: HTTP {response.status_code}")
                    
        except httpx.TimeoutException:
            raise ConnectionError("Sightengine request timed out.")
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error communicating with Sightengine: {e}")
        except Exception as e:
            logger.error(f"SightengineDetector failed: {e}")
            raise
