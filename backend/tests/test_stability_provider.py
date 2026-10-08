import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_providers.stability_provider import StabilityProvider, AIGenerationError
from PIL import Image
import io

@pytest.fixture
def provider():
    with patch("app.core.config.settings.AI_API_KEY", "mock-key"), \
         patch("app.core.config.settings.AI_MODEL", "sd3.5-flash"):
        yield StabilityProvider()

@pytest.mark.asyncio
async def test_successful_generation(provider):
    # Create a 512x512 mock image
    img = Image.new("RGB", (512, 512), color="red")
    out = io.BytesIO()
    img.save(out, format="JPEG")
    mock_bytes = out.getvalue()
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_bytes
        mock_post.return_value = mock_response
        
        result_bytes, name, model = await provider.generate_image("test prompt")
        
        assert name == "stability"
        assert model == "sd3.5-flash"
        assert result_bytes == mock_bytes

@pytest.mark.asyncio
async def test_invalid_image_response(provider):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"not an image"
        mock_post.return_value = mock_response
        
        with pytest.raises(AIGenerationError):
            await provider.generate_image("test")

@pytest.mark.asyncio
async def test_http_401(provider):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with pytest.raises(AIGenerationError) as exc:
            await provider.generate_image("test")
        assert "authentication failed" in str(exc.value)

@pytest.mark.asyncio
async def test_http_402(provider):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_post.return_value = mock_response
        
        with pytest.raises(AIGenerationError) as exc:
            await provider.generate_image("test")
        assert "Insufficient credits" in str(exc.value)

@pytest.mark.asyncio
async def test_http_429(provider):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        with pytest.raises(AIGenerationError) as exc:
            await provider.generate_image("test")
        assert "rate limit exceeded" in str(exc.value)

@pytest.mark.asyncio
async def test_http_500(provider):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with pytest.raises(AIGenerationError) as exc:
            await provider.generate_image("test")
        assert "internal error" in str(exc.value)

@pytest.mark.asyncio
async def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    # The config loads it from process env, so we need to mock config
    with patch("app.core.config.settings.AI_API_KEY", None):
        with pytest.raises(ValueError) as exc:
            StabilityProvider()
        assert "not configured" in str(exc.value)
