"""
backend/app/api/routes/upload.py

POST /upload/validate

Phase 2B-2: validates an uploaded image and returns a structured report.
Does NOT embed a watermark, create a provenance record, or store anything.

This endpoint exists to let clients check whether their image is acceptable
before committing to the full provenance workflow (which will be added in 2B-5).
"""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.image_validation import (
    SUPPORTED_FORMATS,
    SUPPORTED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MIN_DIMENSION,
    MAX_DIMENSION,
    validate_image_bytes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])


class ImageValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    width: int
    height: int
    mode: str
    detected_format: str
    file_size_bytes: int


@router.post(
    "/validate",
    response_model=ImageValidationResponse,
    summary="Validate an uploaded image",
    description=(
        "Accepts a multipart image upload and validates it without storing anything. "
        "Returns the validation result, detected format, dimensions, and any errors.\n\n"
        f"**Supported formats:** {sorted(SUPPORTED_FORMATS)}\n\n"
        f"**Maximum file size:** {MAX_FILE_SIZE_BYTES // (1024*1024)} MB\n\n"
        f"**Minimum dimensions:** {MIN_DIMENSION}×{MIN_DIMENSION} px\n\n"
        f"**Maximum dimensions:** {MAX_DIMENSION}×{MAX_DIMENSION} px"
    ),
    status_code=status.HTTP_200_OK,
)
async def validate_image(
    file: UploadFile = File(..., description="Image file to validate"),
) -> ImageValidationResponse:
    """
    Validate the uploaded image without persisting anything.

    Always returns HTTP 200 with `valid=true/false` in the body.
    HTTP 4xx is only returned for request-level errors (e.g. no file sent).
    """
    if file.filename is None or file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided in upload.",
        )

    raw_bytes = await file.read()

    result = validate_image_bytes(
        raw_bytes,
        declared_content_type=file.content_type,
    )

    return ImageValidationResponse(
        valid=result.valid,
        errors=result.errors,
        width=result.width,
        height=result.height,
        mode=result.mode,
        detected_format=result.detected_format,
        file_size_bytes=result.file_size_bytes,
    )
