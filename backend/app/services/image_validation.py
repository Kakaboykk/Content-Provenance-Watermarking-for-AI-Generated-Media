"""
backend/app/services/image_validation.py

Image upload validation service — pure Python, no FastAPI dependency.

Responsibilities:
  - Check that uploaded bytes are a readable image (PIL decode)
  - Enforce supported MIME / format types
  - Check minimum / maximum dimensions
  - Check color mode (reject palette, CMYK, etc.)
  - Check file size
  - Return a structured validation result

Does NOT:
  - resize, crop, or pad images
  - embed watermarks
  - touch the database

Design note:
  The canonical watermark image is 512×512 RGB (spec §1).
  The preprocessing step (watermark/preprocess.py) will resize to 512×512
  before embedding, so we do NOT require the upload to already be 512×512.
  We do require:
    - minimum dimension: 64×64   (below this, resize to 512×512 would be extreme)
    - maximum dimension: 8192×8192 (sane upper bound to prevent DoS)
    - supported formats: JPEG, PNG, WEBP, BMP, TIFF
    - maximum file size: 20 MB
    - mode: must be convertible to RGB (rejecting raw palette-only images
            that have no palette fallback — PIL will raise on decode anyway)
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Literal

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — validated against the frozen spec and Phase 1 findings
# ---------------------------------------------------------------------------
SUPPORTED_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP", "BMP", "TIFF"})
SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }
)
MIN_DIMENSION: int = 64       # pixels (width and height both)
MAX_DIMENSION: int = 8192     # pixels
MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

# Modes that PIL can reliably convert to RGB
_CONVERTIBLE_MODES: frozenset[str] = frozenset(
    {"RGB", "RGBA", "L", "LA", "P", "PA", "1", "I", "F"}
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class ImageValidationResult:
    """
    Structured result returned by validate_image_bytes().

    Attributes:
        valid:        True only if ALL checks passed.
        errors:       List of human-readable error messages (empty when valid).
        width:        Decoded image width in pixels (0 if decoding failed).
        height:       Decoded image height in pixels (0 if decoding failed).
        mode:         PIL image mode (empty string if decoding failed).
        detected_format: PIL-detected format string (e.g. "JPEG", "PNG").
        file_size_bytes: Size of the raw bytes received.
    """
    valid: bool
    errors: list[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    mode: str = ""
    detected_format: str = ""
    file_size_bytes: int = 0


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------
def validate_image_bytes(
    data: bytes,
    *,
    declared_content_type: str | None = None,
) -> ImageValidationResult:
    """
    Validate raw image bytes.

    Args:
        data:                   Raw bytes from the uploaded file.
        declared_content_type:  The Content-Type header value supplied by the
                                client (used for an early MIME check only; we
                                always verify against the actual decoded format).

    Returns:
        ImageValidationResult with .valid=True when all checks pass.
    """
    errors: list[str] = []
    result = ImageValidationResult(valid=False, file_size_bytes=len(data))

    # ── 1. File size ────────────────────────────────────────────────────────
    if len(data) == 0:
        errors.append("Uploaded file is empty.")
        result.errors = errors
        return result

    if len(data) > MAX_FILE_SIZE_BYTES:
        errors.append(
            f"File size {len(data):,} bytes exceeds the maximum "
            f"of {MAX_FILE_SIZE_BYTES:,} bytes (20 MB)."
        )
        result.errors = errors
        return result

    # ── 2. Declared MIME type (advisory — we still decode to confirm) ───────
    if declared_content_type is not None:
        # Strip parameters like "; charset=utf-8"
        mime_base = declared_content_type.split(";")[0].strip().lower()
        if mime_base not in SUPPORTED_MIME_TYPES:
            errors.append(
                f"Declared Content-Type {declared_content_type!r} is not supported. "
                f"Supported types: {sorted(SUPPORTED_MIME_TYPES)}"
            )
            # Don't abort yet — still try to decode; the declared type might be wrong

    # ── 3. Actual image decoding ────────────────────────────────────────────
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()               # raises on corrupt files, stops PIL deferred reading
    except UnidentifiedImageError:
        errors.append(
            "The uploaded file could not be identified as an image. "
            "It may be corrupted or an unsupported format."
        )
        result.errors = errors
        return result
    except Exception as exc:
        errors.append(f"Image decoding failed: {exc}")
        result.errors = errors
        return result

    # Re-open after verify() — verify() closes the internal fp
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as exc:
        errors.append(f"Image could not be re-opened after verification: {exc}")
        result.errors = errors
        return result

    detected_format = img.format or ""
    result.detected_format = detected_format
    result.width, result.height = img.size
    result.mode = img.mode

    # ── 4. Format whitelist ─────────────────────────────────────────────────
    if detected_format not in SUPPORTED_FORMATS:
        errors.append(
            f"Image format {detected_format!r} is not supported. "
            f"Supported formats: {sorted(SUPPORTED_FORMATS)}"
        )

    # ── 5. Dimensions ───────────────────────────────────────────────────────
    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        errors.append(
            f"Image dimensions {w}×{h} are below the minimum "
            f"{MIN_DIMENSION}×{MIN_DIMENSION} pixels."
        )
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        errors.append(
            f"Image dimensions {w}×{h} exceed the maximum "
            f"{MAX_DIMENSION}×{MAX_DIMENSION} pixels."
        )

    # ── 6. Color mode (must be convertible to RGB) ─────────────────────────
    if img.mode not in _CONVERTIBLE_MODES:
        errors.append(
            f"Image mode {img.mode!r} cannot be converted to RGB. "
            f"Supported modes: {sorted(_CONVERTIBLE_MODES)}"
        )

    result.valid = len(errors) == 0
    result.errors = errors

    if result.valid:
        logger.debug(
            "Image validation passed: format=%s mode=%s size=%dx%d bytes=%d",
            detected_format, img.mode, w, h, len(data),
        )
    else:
        logger.info("Image validation failed: %s", errors)

    return result
