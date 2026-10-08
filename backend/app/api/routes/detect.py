"""
backend/app/api/routes/detect.py

POST /detect-ai

Phase 5B: AI Image Detection Endpoint.
Accepts an image and runs a probabilistic AI-generated vs human-generated classification.
"""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.ai_detectors import get_ai_detector
from app.services.image_validation import validate_image_bytes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detect-ai", tags=["AI Image Detection"])


class AIDetectionResponse(BaseModel):
    label: str
    confidence: float
    provider: str
    model: str


@router.post(
    "",
    summary="Probabilistic AI-generated image detection",
    description=(
        "Accepts an image file and analyzes it to determine if it is likely AI-generated.\n"
        "Returns a normalized confidence value (0.0 to 1.0) and a label:\n"
        "- `AI_GENERATED`\n"
        "- `LIKELY_HUMAN`\n"
        "- `UNCERTAIN`\n\n"
        "NOTE: This is a probabilistic classification, not cryptographic proof."
    ),
    response_model=AIDetectionResponse,
    status_code=status.HTTP_200_OK,
)
async def detect_ai_endpoint(file: UploadFile = File(...)) -> AIDetectionResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided in upload."
        )

    raw_bytes = await file.read()

    # Reuse existing image validation to prevent processing corrupt/invalid types
    val_result = validate_image_bytes(raw_bytes, declared_content_type=file.content_type)
    if not val_result.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image validation failed: {', '.join(val_result.errors)}"
        )

    # Initialize configured detector provider
    try:
        detector = get_ai_detector()
    except Exception as exc:
        logger.error(f"Detector configuration error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI detection is misconfigured on the server."
        )

    # Analyze image
    result = await detector.detect_image(raw_bytes)

    return AIDetectionResponse(
        label=result.get("label", "UNCERTAIN"),
        confidence=float(result.get("confidence", 0.0)),
        provider=str(result.get("provider", "unknown")),
        model=str(result.get("model", "unknown")),
    )
