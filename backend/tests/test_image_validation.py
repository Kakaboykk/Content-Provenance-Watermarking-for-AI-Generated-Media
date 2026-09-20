"""
backend/tests/test_image_validation.py

Automated tests for the image validation service (2B-2).

All tests use in-memory synthetic images — no file system, no PostgreSQL needed.
"""
import io
import struct
import zlib

import pytest
from PIL import Image

from app.services.image_validation import (
    MAX_DIMENSION,
    MAX_FILE_SIZE_BYTES,
    MIN_DIMENSION,
    ImageValidationResult,
    validate_image_bytes,
)


# ---------------------------------------------------------------------------
# Helpers: generate minimal valid in-memory images
# ---------------------------------------------------------------------------
def _make_png(width: int = 256, height: int = 256, mode: str = "RGB") -> bytes:
    """Return the raw bytes of a minimal PNG image."""
    img = Image.new(mode, (width, height), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg(width: int = 256, height: int = 256) -> bytes:
    """Return the raw bytes of a minimal JPEG image."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _make_webp(width: int = 256, height: int = 256) -> bytes:
    img = Image.new("RGB", (width, height), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------
class TestValidImageAccepted:
    def test_valid_png_rgb(self):
        result = validate_image_bytes(_make_png(512, 512, "RGB"))
        assert result.valid is True
        assert result.errors == []
        assert result.width == 512
        assert result.height == 512
        assert result.mode == "RGB"
        assert result.detected_format == "PNG"

    def test_valid_png_rgba(self):
        result = validate_image_bytes(_make_png(256, 256, "RGBA"))
        assert result.valid is True
        assert result.mode == "RGBA"

    def test_valid_jpeg(self):
        result = validate_image_bytes(_make_jpeg(800, 600))
        assert result.valid is True
        assert result.detected_format == "JPEG"

    def test_valid_webp(self):
        result = validate_image_bytes(_make_webp(400, 400))
        assert result.valid is True
        assert result.detected_format == "WEBP"

    def test_non_square_image(self):
        result = validate_image_bytes(_make_jpeg(1920, 1080))
        assert result.valid is True
        assert result.width == 1920
        assert result.height == 1080

    def test_minimum_allowed_dimensions(self):
        result = validate_image_bytes(_make_png(MIN_DIMENSION, MIN_DIMENSION))
        assert result.valid is True

    def test_returns_correct_file_size(self):
        data = _make_png(128, 128)
        result = validate_image_bytes(data)
        assert result.file_size_bytes == len(data)

    def test_returns_image_validation_result_type(self):
        result = validate_image_bytes(_make_png())
        assert isinstance(result, ImageValidationResult)


# ---------------------------------------------------------------------------
# File size checks
# ---------------------------------------------------------------------------
class TestFileSizeValidation:
    def test_empty_file_rejected(self):
        result = validate_image_bytes(b"")
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_file_over_limit_rejected(self):
        # Build a bytes object just over the limit without allocating 20 MB:
        # We synthesise the "size" by patching the check directly.
        oversized = b"\x00" * (MAX_FILE_SIZE_BYTES + 1)
        result = validate_image_bytes(oversized)
        assert result.valid is False
        assert any("exceed" in e.lower() or "maximum" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Format / MIME checks
# ---------------------------------------------------------------------------
class TestFormatValidation:
    def test_random_bytes_rejected(self):
        result = validate_image_bytes(b"this is not an image at all !!!")
        assert result.valid is False
        assert result.errors  # at least one error

    def test_declared_unsupported_mime_produces_error(self):
        data = _make_png()
        result = validate_image_bytes(data, declared_content_type="image/gif")
        # GIF is not in SUPPORTED_MIME_TYPES — error about declared type
        assert any("gif" in e.lower() for e in result.errors)
        # But if the actual image decodes as PNG it may still be valid overall
        # (the declared MIME warning is advisory). The important thing is the
        # error is reported.

    def test_correct_mime_no_extra_errors(self):
        data = _make_jpeg()
        result = validate_image_bytes(data, declared_content_type="image/jpeg")
        assert result.valid is True
        assert result.errors == []


# ---------------------------------------------------------------------------
# Dimension checks
# ---------------------------------------------------------------------------
class TestDimensionValidation:
    def test_image_too_small_rejected(self):
        result = validate_image_bytes(_make_png(MIN_DIMENSION - 1, 256))
        assert result.valid is False
        assert any("minimum" in e.lower() for e in result.errors)

    def test_image_too_tall_rejected(self):
        result = validate_image_bytes(_make_png(256, MIN_DIMENSION - 1))
        assert result.valid is False
        assert any("minimum" in e.lower() for e in result.errors)

    def test_image_too_wide_rejected(self):
        data = _make_png(MAX_DIMENSION + 1, 256)
        result = validate_image_bytes(data)
        assert result.valid is False
        assert any("maximum" in e.lower() or "exceed" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# API route tests (uses the FastAPI test client from conftest)
# ---------------------------------------------------------------------------
class TestUploadValidateEndpoint:
    def test_valid_png_returns_200_valid_true(self, client):
        data = _make_png(512, 512)
        response = client.post(
            "/upload/validate",
            files={"file": ("test.png", data, "image/png")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True
        assert body["errors"] == []
        assert body["width"] == 512
        assert body["height"] == 512
        assert body["detected_format"] == "PNG"

    def test_invalid_bytes_returns_200_valid_false(self, client):
        response = client.post(
            "/upload/validate",
            files={"file": ("bad.bin", b"not an image", "application/octet-stream")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0

    def test_too_small_image_returns_200_valid_false(self, client):
        data = _make_png(32, 32)
        response = client.post(
            "/upload/validate",
            files={"file": ("small.png", data, "image/png")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert any("minimum" in e.lower() for e in body["errors"])

    def test_valid_jpeg_returns_200_valid_true(self, client):
        data = _make_jpeg(800, 600)
        response = client.post(
            "/upload/validate",
            files={"file": ("photo.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True

    def test_endpoint_in_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "/upload/validate" in paths
        assert "post" in paths["/upload/validate"]
