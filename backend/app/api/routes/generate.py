"""
backend/app/api/routes/generate.py

POST /generate

Phase 3 Step 2: AI Generation API Endpoint.
Accepts a prompt and returns the AI-generated image along with metadata headers.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.ai_generation import generate_image, AIGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["AI Generation"])


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="The text prompt for image generation.")


@router.post(
    "",
    summary="Generate an AI Image from a prompt",
    description=(
        "Takes a text prompt and returns an AI-generated image.\n"
        "Returns the image bytes directly (e.g., image/png) along with "
        "custom headers indicating the AI provider and model used."
    ),
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def generate_endpoint(
    request: GenerateRequest,
) -> Response:
    try:
        # Call the Phase 3 Step 1 AI Generation Service
        image_bytes, provider, model = await generate_image(request.prompt)
    except AIGenerationError as exc:
        logger.error(f"AI Generation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Unexpected error during AI Generation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during image generation."
        )

    # Return the raw image bytes. We'll use custom headers to bubble up the provider and model
    # so the frontend can capture them for the subsequent provenance registration step.
    headers = {
        "X-AI-Provider": provider,
        "X-AI-Model": model,
        "Content-Disposition": 'attachment; filename="generated_image.png"',
    }

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers=headers,
    )
