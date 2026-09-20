"""
backend/app/services/watermark.py

Service layer bridging the Phase 0 watermark algorithm with the backend bytes-oriented API.

This module is responsible for:
  - Decoding image bytes to a PIL Image
  - Calling the Phase 0 embed_watermark function
  - Encoding the watermarked PIL Image back to lossless PNG bytes
"""
import io
import logging
import uuid
from PIL import Image

from watermark.embed import embed_watermark
from watermark.config import DELTA_INITIAL

logger = logging.getLogger(__name__)


class WatermarkServiceError(Exception):
    """Raised when the watermark embedding process fails."""


def embed_watermark_in_bytes(
    image_bytes: bytes, 
    provenance_uuid: uuid.UUID,
    delta: float = DELTA_INITIAL,
) -> bytes:
    """
    Embed a provenance UUID into the provided image bytes using the Phase 0 engine.

    Args:
        image_bytes: Raw bytes of the validated input image.
        provenance_uuid: The UUID to embed.
        delta: The QIM quantization step size (defaults to Phase 0 baseline).

    Returns:
        The raw bytes of the watermarked image encoded as a lossless PNG.

    Raises:
        WatermarkServiceError: If decoding, embedding, or encoding fails.
    """
    try:
        # Load image from bytes (must have been validated beforehand)
        img = Image.open(io.BytesIO(image_bytes))
        
        # Ensure image is fully loaded before processing
        img.load()
    except Exception as exc:
        raise WatermarkServiceError(f"Failed to decode image bytes: {exc}") from exc

    try:
        # Call Phase 0 watermark engine
        watermarked_img = embed_watermark(img, provenance_uuid, delta=delta)
    except Exception as exc:
        logger.error("Phase 0 engine failed during embedding: %s", exc)
        raise WatermarkServiceError(f"Watermark embedding failed: {exc}") from exc

    try:
        # Encode back to lossless PNG bytes
        out_buf = io.BytesIO()
        watermarked_img.save(out_buf, format="PNG", optimize=False)
        out_bytes = out_buf.getvalue()
        
        logger.info(
            "Watermark embedded successfully for UUID %s (PNG size: %d bytes)", 
            provenance_uuid, len(out_bytes)
        )
        return out_bytes
    except Exception as exc:
        raise WatermarkServiceError(f"Failed to encode watermarked image to PNG: {exc}") from exc
