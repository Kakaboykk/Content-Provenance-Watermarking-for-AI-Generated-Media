"""
backend/app/services/ai_providers/huggingface_provider.py

Real AI generation provider using the Hugging Face Inference API.
"""
import logging
import io
from typing import Tuple

from huggingface_hub import AsyncInferenceClient
from huggingface_hub.errors import (
    HfHubHTTPError,
    BadRequestError,
    LocalTokenNotFoundError,
)

from .base import BaseAIProvider
from .mock_provider import AIGenerationError
from app.core.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseAIProvider):
    """
    Calls the Hugging Face Serverless Inference API to generate images
    using the huggingface_hub InferenceClient.
    """

    def __init__(self):
        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is not configured for HuggingFaceProvider.")
            
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL or "black-forest-labs/FLUX.1-schnell"
        
        # We explicitly set provider to None to use default logic, or we could set it to "auto"
        # Since huggingface_hub has its own routing for serverless inference.
        self.client = AsyncInferenceClient(
            model=self.model,
            token=self.api_key,
            timeout=60.0,
        )

    async def generate_image(self, prompt: str) -> Tuple[bytes, str, str]:
        logger.info(f"[HuggingFaceProvider] Requesting image for prompt: {prompt!r} using model {self.model}")
        
        try:
            # text_to_image returns a PIL Image
            pil_image = await self.client.text_to_image(prompt=prompt)
            
            # Convert PIL image to PNG bytes
            out_buf = io.BytesIO()
            pil_image.convert("RGB").save(out_buf, format="PNG")
            image_bytes = out_buf.getvalue()
            
            if not image_bytes:
                raise AIGenerationError("AI Provider returned an empty image.")
                
            return image_bytes, "huggingface", self.model
            
        except HfHubHTTPError as e:
            # e.response is a requests.Response or httpx.Response depending on backend
            status_code = getattr(e.response, "status_code", 500)
            logger.error(f"Hugging Face HTTP error {status_code}: {e}")
            
            if status_code == 401:
                raise AIGenerationError("AI Provider authentication failed. Please check the AI_API_KEY.")
            elif status_code == 429:
                raise AIGenerationError("AI Provider rate limit exceeded. Please try again later.")
            elif status_code == 503:
                # e.g., Model is loading
                raise AIGenerationError("AI Model is currently loading or unavailable. Please try again in a moment.")
            elif status_code == 403:
                raise AIGenerationError(f"AI Provider access forbidden. Your API token might lack permissions to run '{self.model}'.")
            elif status_code == 404:
                raise AIGenerationError(f"Model {self.model} not found or unsupported on the Inference API.")
            else:
                raise AIGenerationError(f"AI Provider returned an error: HTTP {status_code}")
                
        except BadRequestError as e:
            logger.error(f"Hugging Face bad request: {e}")
            raise AIGenerationError(f"AI Provider rejected the request: {e}")
            
        except LocalTokenNotFoundError:
            raise AIGenerationError("AI_API_KEY token is missing or invalid.")
            
        except Exception as e:
            logger.error(f"Unexpected error in HuggingFaceProvider: {e}")
            # Do not expose the exact exception to the client if it contains secrets,
            # but provide enough context.
            error_str = str(e)
            if self.api_key and self.api_key in error_str:
                error_str = error_str.replace(self.api_key, "***")
                
            raise AIGenerationError(f"An unexpected error occurred during AI generation: {error_str}")
