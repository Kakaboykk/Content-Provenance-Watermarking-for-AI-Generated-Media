import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_detectors.sightengine_detector import SightengineDetector

@pytest.fixture
def detector():
    with patch("app.core.config.settings.SIGHTENGINE_API_USER", "user"), \
         patch("app.core.config.settings.SIGHTENGINE_API_SECRET", "secret"), \
         patch("app.core.config.settings.AI_DETECTOR_THRESHOLD", 0.70):
        yield SightengineDetector()

@pytest.mark.asyncio
async def test_ai_generated_classification(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "type": {"ai_generated": 0.95, "human": 0.05}
        }
        mock_post.return_value = mock_response
        
        result = await detector.detect_image(b"fakebytes")
        assert result["label"] == "AI_GENERATED"
        assert result["confidence"] == 0.95
        assert result["provider"] == "sightengine"
        assert result["model"] == "genai"

@pytest.mark.asyncio
async def test_likely_human_classification(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "type": {"ai_generated": 0.1, "human": 0.85}
        }
        mock_post.return_value = mock_response
        
        result = await detector.detect_image(b"fakebytes")
        assert result["label"] == "LIKELY_HUMAN"
        assert result["confidence"] == 0.85

@pytest.mark.asyncio
async def test_uncertain_classification(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "type": {"ai_generated": 0.6, "human": 0.5}
        }
        mock_post.return_value = mock_response
        
        result = await detector.detect_image(b"fakebytes")
        assert result["label"] == "UNCERTAIN"
        assert result["confidence"] == 0.6  # max of both

@pytest.mark.asyncio
async def test_missing_credentials():
    with patch("app.core.config.settings.SIGHTENGINE_API_USER", None):
        with pytest.raises(ValueError) as exc:
            SightengineDetector()
        assert "not configured" in str(exc.value)

@pytest.mark.asyncio
async def test_http_401(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with pytest.raises(PermissionError) as exc:
            await detector.detect_image(b"fakebytes")
        assert "authentication failed" in str(exc.value)

@pytest.mark.asyncio
async def test_malformed_response(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        with pytest.raises(ValueError) as exc:
            await detector.detect_image(b"fakebytes")
        assert "malformed JSON" in str(exc.value)

@pytest.mark.asyncio
async def test_missing_fields_response(detector):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "type": {}
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(ValueError) as exc:
            await detector.detect_image(b"fakebytes")
        assert "Missing" in str(exc.value)
