"""
backend/tests/test_ai_providers.py

Tests for the AI Generation providers and factory.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from PIL import Image

from app.services.ai_providers import get_ai_provider, AIGenerationError
from app.services.ai_providers.mock_provider import MockAIProvider
from app.services.ai_providers.huggingface_provider import HuggingFaceProvider
from app.core.config import settings

def test_get_mock_provider(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)

def test_get_huggingface_provider(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "huggingface")
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    provider = get_ai_provider()
    assert isinstance(provider, HuggingFaceProvider)

def test_get_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "invalid-provider")
    with pytest.raises(ValueError, match="Unknown AI_PROVIDER configured"):
        get_ai_provider()

def test_huggingface_provider_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "huggingface")
    monkeypatch.setattr(settings, "AI_API_KEY", None)
    with pytest.raises(ValueError, match="AI_API_KEY is not configured"):
        HuggingFaceProvider()

@pytest.mark.asyncio
async def test_mock_provider_generation():
    provider = MockAIProvider()
    image_bytes, provider_name, model_name = await provider.generate_image("test prompt")
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    assert provider_name in ("stability-ai-mock", "local-mock")
    assert model_name in ("stable-diffusion-v1-5-mock", "pillow-dynamic-mock")

@pytest.mark.asyncio
async def test_huggingface_provider_success(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_MODEL", "test-model")
    
    provider = HuggingFaceProvider()
    
    # Mock the AsyncInferenceClient's text_to_image method
    mock_pil = Image.new("RGB", (10, 10))
    provider.client.text_to_image = AsyncMock(return_value=mock_pil)
    
    image_bytes, provider_name, model_name = await provider.generate_image("a sunset")
    
    # Check it produced PNG bytes
    assert image_bytes.startswith(b"\x89PNG")
    assert provider_name == "huggingface"
    assert model_name == "test-model"

@pytest.mark.asyncio
async def test_huggingface_provider_http_error(monkeypatch):
    from huggingface_hub.errors import HfHubHTTPError
    
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    provider = HuggingFaceProvider()
    
    # Create a mock response for the error
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    provider.client.text_to_image = AsyncMock(side_effect=HfHubHTTPError("Server Error", response=mock_response))
    
    with pytest.raises(AIGenerationError, match="HTTP 500"):
        await provider.generate_image("a sunset")

@pytest.mark.asyncio
async def test_huggingface_provider_authentication_error(monkeypatch):
    from huggingface_hub.errors import HfHubHTTPError
    
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    provider = HuggingFaceProvider()
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    provider.client.text_to_image = AsyncMock(side_effect=HfHubHTTPError("Unauthorized", response=mock_response))
    
    with pytest.raises(AIGenerationError, match="authentication failed"):
        await provider.generate_image("a sunset")
