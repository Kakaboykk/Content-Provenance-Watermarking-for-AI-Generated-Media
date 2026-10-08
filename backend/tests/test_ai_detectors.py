"""
backend/tests/test_ai_detectors.py

Tests for the AI Image Detection providers and factory.
"""
import pytest
from unittest.mock import MagicMock

from app.services.ai_detectors import get_ai_detector
from app.services.ai_detectors.mock_detector import MockAIDetector
from app.services.ai_detectors.huggingface_detector import HuggingFaceDetector
from app.core.config import settings
from fastapi import HTTPException

import httpx

# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

def test_get_mock_detector(monkeypatch):
    monkeypatch.setattr(settings, "AI_DETECTOR_PROVIDER", "mock")
    detector = get_ai_detector()
    assert isinstance(detector, MockAIDetector)


def test_get_huggingface_detector(monkeypatch):
    monkeypatch.setattr(settings, "AI_DETECTOR_PROVIDER", "huggingface")
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = get_ai_detector()
    assert isinstance(detector, HuggingFaceDetector)


def test_get_unknown_detector(monkeypatch):
    monkeypatch.setattr(settings, "AI_DETECTOR_PROVIDER", "invalid-provider")
    with pytest.raises(ValueError, match="Unknown AI_DETECTOR_PROVIDER configured"):
        get_ai_detector()


def test_huggingface_detector_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "AI_DETECTOR_PROVIDER", "huggingface")
    monkeypatch.setattr(settings, "AI_API_KEY", None)
    with pytest.raises(ValueError, match="AI_API_KEY is not configured"):
        HuggingFaceDetector()


# ---------------------------------------------------------------------------
# Mock detector tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_detector_labels():
    detector = MockAIDetector()

    # size % 3 == 0 -> AI_GENERATED
    result_ai = await detector.detect_image(b"123")
    assert result_ai["label"] == "AI_GENERATED"
    assert result_ai["confidence"] == 0.95
    assert result_ai["provider"] == "mock"

    # size % 3 == 1 -> LIKELY_HUMAN
    result_human = await detector.detect_image(b"1234")
    assert result_human["label"] == "LIKELY_HUMAN"
    assert result_human["provider"] == "mock"

    # size % 3 == 2 -> UNCERTAIN
    result_unc = await detector.detect_image(b"12345")
    assert result_unc["label"] == "UNCERTAIN"
    assert result_unc["provider"] == "mock"


# ---------------------------------------------------------------------------
# HuggingFaceDetector label/score mapping tests
# ---------------------------------------------------------------------------

def _make_mock_client(predictions: list[dict], status_code: int = 200, text: str = ""):
    """Returns an httpx.AsyncClient context-manager mock with given predictions."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = predictions
    mock_response.text = text

    class MockAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, headers, content):
            # Verify required headers
            assert "Authorization" in headers
            assert headers["Content-Type"] == "image/jpeg"
            return mock_response

    return MockAsyncClient()


@pytest.mark.asyncio
async def test_hf_fake_high_confidence_ai_generated(monkeypatch):
    """FAKE=0.95, REAL=0.05 -> AI_GENERATED at 0.95"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "FAKE", "score": 0.95},
            {"label": "REAL", "score": 0.05},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "AI_GENERATED"
    assert result["confidence"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_hf_real_high_confidence_likely_human(monkeypatch):
    """FAKE=0.05, REAL=0.95 -> LIKELY_HUMAN at 0.95"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "REAL", "score": 0.95},
            {"label": "FAKE", "score": 0.05},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "LIKELY_HUMAN"
    assert result["confidence"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_hf_uncertain_ai_slightly_above_50(monkeypatch):
    """FAKE=0.52, REAL=0.48 below threshold -> UNCERTAIN"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "FAKE", "score": 0.52},
            {"label": "REAL", "score": 0.48},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "UNCERTAIN"
    assert result["confidence"] == pytest.approx(0.52)


@pytest.mark.asyncio
async def test_hf_uncertain_human_slightly_above_50(monkeypatch):
    """FAKE=0.48, REAL=0.52 below threshold -> UNCERTAIN"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "FAKE", "score": 0.48},
            {"label": "REAL", "score": 0.52},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "UNCERTAIN"
    assert result["confidence"] == pytest.approx(0.52)


@pytest.mark.asyncio
async def test_hf_ai_exactly_at_threshold(monkeypatch):
    """FAKE exactly at threshold -> AI_GENERATED"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "FAKE", "score": 0.70},
            {"label": "REAL", "score": 0.30},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "AI_GENERATED"
    assert result["confidence"] == pytest.approx(0.70)


@pytest.mark.asyncio
async def test_hf_human_exactly_at_threshold(monkeypatch):
    """REAL exactly at threshold -> LIKELY_HUMAN"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "REAL", "score": 0.70},
            {"label": "FAKE", "score": 0.30},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "LIKELY_HUMAN"
    assert result["confidence"] == pytest.approx(0.70)


@pytest.mark.asyncio
async def test_hf_unknown_label_becomes_uncertain(monkeypatch):
    """Completely unrecognised labels -> UNCERTAIN"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "CATEGORY_A", "score": 0.98},
            {"label": "CATEGORY_B", "score": 0.02},
        ])
    )

    result = await detector.detect_image(b"img")
    assert result["label"] == "UNCERTAIN"
    assert result["confidence"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_hf_malformed_response(monkeypatch):
    """Empty/malformed response -> 502"""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([])          # empty list
    )

    with pytest.raises(HTTPException) as exc:
        await detector.detect_image(b"img")
    assert exc.value.status_code == 502


# ---------------------------------------------------------------------------
# HTTP error handling tests
# ---------------------------------------------------------------------------

def _make_http_error_client(status_code: int):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = f"HTTP {status_code} error"

    class MockAsyncClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, headers, content):
            return mock_response

    return MockAsyncClient()


@pytest.mark.asyncio
async def test_hf_http_401(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = HuggingFaceDetector()
    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_http_error_client(401)
    )
    with pytest.raises(HTTPException) as exc:
        await detector.detect_image(b"img")
    assert exc.value.status_code == 502
    assert "authentication" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_hf_http_429(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = HuggingFaceDetector()
    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_http_error_client(429)
    )
    with pytest.raises(HTTPException) as exc:
        await detector.detect_image(b"img")
    assert exc.value.status_code == 502
    assert "rate limit" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_hf_http_503(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = HuggingFaceDetector()
    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_http_error_client(503)
    )
    with pytest.raises(HTTPException) as exc:
        await detector.detect_image(b"img")
    assert exc.value.status_code == 502
    assert "unavailable" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_hf_network_failure(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    detector = HuggingFaceDetector()

    class MockNetworkErrorClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, headers, content):
            raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: MockNetworkErrorClient()
    )
    with pytest.raises(HTTPException) as exc:
        await detector.detect_image(b"img")
    assert exc.value.status_code == 502
    assert "network" in exc.value.detail.lower()


# ---------------------------------------------------------------------------
# Label normalization using alternative model label vocabularies
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hf_label_artificial_maps_to_ai(monkeypatch):
    """'artificial' label should map to AI_GENERATED."""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "artificial", "score": 0.91},
            {"label": "natural", "score": 0.09},
        ])
    )
    result = await detector.detect_image(b"img")
    assert result["label"] == "AI_GENERATED"
    assert result["confidence"] == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_hf_label_real_at_top_still_maps_correctly(monkeypatch):
    """REAL listed first but lower score than FAKE -> AI_GENERATED."""
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "AI_DETECTOR_THRESHOLD", 0.70)
    detector = HuggingFaceDetector()

    # Model may return sorted by score (highest first), but let's test reversed order
    monkeypatch.setattr(
        "app.services.ai_detectors.huggingface_detector.httpx.AsyncClient",
        lambda **kwargs: _make_mock_client([
            {"label": "REAL", "score": 0.23},
            {"label": "FAKE", "score": 0.77},
        ])
    )
    result = await detector.detect_image(b"img")
    assert result["label"] == "AI_GENERATED"
    assert result["confidence"] == pytest.approx(0.77)
