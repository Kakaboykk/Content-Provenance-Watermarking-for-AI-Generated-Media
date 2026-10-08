"""
backend/app/services/ai_providers/stability_provider.py

Real AI generation provider using Stability AI.
"""
import logging
import io
from typing import Tuple

import httpx
from PIL import Image

from .base import BaseAIProvider
from .mock_provider import AIGenerationError
from app.core.config import settings

logger = logging.getLogger(__name__)


class StabilityProvider(BaseAIProvider):
    """
    Calls Stability AI REST API to generate images.
    """

    def __init__(self):
        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is not configured for StabilityProvider.")
            
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL or "sd3.5-flash"
        self.base_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    async def generate_image(self, prompt: str) -> Tuple[bytes, str, str]:
        logger.info(f"[StabilityProvider] Requesting image for prompt: {prompt!r} using model {self.model}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",
        }
        
        # Stability AI expects multipart/form-data.
        # With httpx, we can force this by passing string fields via `files` or `data` along with a dummy file,
        # but the cleanest way is to use `data` with an empty `files` dict, or construct multipart explicitly.
        # We will use `files` with (None, value) to force multipart encoding for all text fields.
        multipart_data = {
            "prompt": (None, prompt),
            "mode": (None, "text-to-image"),
            "model": (None, self.model),
            "output_format": (None, "jpeg"),
            "width": (None, str(512)),
            "height": (None, str(512)),
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    files=multipart_data
                )
                
                if response.status_code == 200:
                    image_bytes = response.content
                    if not image_bytes:
                        raise AIGenerationError("AI Provider returned an empty image.")
                        
                    # Basic validation of the image dimensions
                    try:
                        img = Image.open(io.BytesIO(image_bytes))
                        if img.size != (512, 512):
                            logger.warning(f"Provider returned {img.size}, resizing to 512x512.")
                            img = img.resize((512, 512))
                            out_buf = io.BytesIO()
                            # Maintain JPEG format if it was returned as JPEG
                            format_to_save = img.format if img.format else "JPEG"
                            img.save(out_buf, format=format_to_save)
                            image_bytes = out_buf.getvalue()
                    except Exception as e:
                        logger.error(f"Failed to validate/resize image: {e}")
                        raise AIGenerationError("AI Provider returned invalid image bytes.")
                        
                    return image_bytes, "stability", self.model
                
                elif response.status_code == 401:
                    raise AIGenerationError("AI Provider authentication failed. Please check the AI_API_KEY.")
                elif response.status_code == 402:
                    raise AIGenerationError("Insufficient credits for AI Provider.")
                elif response.status_code == 429:
                    raise AIGenerationError("AI Provider rate limit exceeded. Please try again later.")
                elif response.status_code >= 500:
                    raise AIGenerationError(f"AI Provider internal error: HTTP {response.status_code}")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("errors", str(error_data))
                    except Exception:
                        error_msg = response.text
                    raise AIGenerationError(f"AI Provider returned an error: HTTP {response.status_code} - {error_msg}")
                    
        except httpx.TimeoutException:
            raise AIGenerationError("AI Provider request timed out.")
        except httpx.RequestError as e:
            raise AIGenerationError(f"Network error communicating with AI Provider: {e}")
        except AIGenerationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in StabilityProvider: {e}")
            error_str = str(e)
            if self.api_key and self.api_key in error_str:
                error_str = error_str.replace(self.api_key, "***")
            raise AIGenerationError(f"An unexpected error occurred during AI generation: {error_str}")
