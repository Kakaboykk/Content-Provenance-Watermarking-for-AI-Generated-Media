"""
backend/tests/test_watermark_service.py

Automated tests for the watermark integration service.
Verifies that the backend correctly wraps the Phase 0 engine.
"""
import io
import uuid
import pytest
from PIL import Image

from app.services.watermark import embed_watermark_in_bytes, WatermarkServiceError
from watermark.extract import extract_watermark


def _make_dummy_image(width=512, height=512, color=(100, 150, 200)) -> bytes:
    """Create a minimal RGB JPEG image for embedding."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class TestWatermarkService:

    def test_embed_and_extract_roundtrip(self):
        """Test that embedding bytes produces bytes from which we can extract the same UUID."""
        original_bytes = _make_dummy_image()
        target_uuid = uuid.uuid4()
        
        # 1. Embed using the service
        watermarked_bytes = embed_watermark_in_bytes(original_bytes, target_uuid)
        
        # Ensure it returns something and the size is reasonable for a 512x512 PNG
        assert len(watermarked_bytes) > 1024
        
        # Ensure it's a valid PNG
        img = Image.open(io.BytesIO(watermarked_bytes))
        assert img.format == "PNG"
        assert img.size == (512, 512)
        
        # 2. Extract using Phase 0 directly to verify the service did the right thing
        verdict, extracted_uuid = extract_watermark(img)
        
        assert verdict == "AUTHENTIC_UNMODIFIED"
        assert extracted_uuid == target_uuid

    def test_embed_invalid_bytes_raises_error(self):
        """Test that passing garbage bytes raises the custom service error."""
        invalid_bytes = b"not an image at all"
        target_uuid = uuid.uuid4()
        
        with pytest.raises(WatermarkServiceError) as exc_info:
            embed_watermark_in_bytes(invalid_bytes, target_uuid)
            
        assert "decode image bytes" in str(exc_info.value)

    def test_embed_returns_deterministic_format(self):
        """Test that the output is ALWAYS a lossless PNG, even if input was JPEG."""
        jpeg_bytes = _make_dummy_image()
        target_uuid = uuid.uuid4()
        
        out_bytes = embed_watermark_in_bytes(jpeg_bytes, target_uuid)
        
        # Decode and verify format is explicitly PNG
        img = Image.open(io.BytesIO(out_bytes))
        assert img.format == "PNG"
