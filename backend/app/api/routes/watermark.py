"""
backend/app/api/routes/watermark.py

POST /watermark/embed

Phase 2B-5: End-to-End Workflow integration.
Accepts an image upload, validates it, creates a provenance record, 
embeds a watermark, records the asset in the database, and returns the watermarked PNG.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.image_validation import validate_image_bytes
from app.services.provenance import create_provenance_record
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.watermark import embed_watermark_in_bytes, WatermarkServiceError
from app.services.asset import register_watermarked_asset, AssetServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watermark", tags=["Watermark End-to-End"])


@router.post(
    "/embed",
    summary="Embed a provenance watermark into an uploaded image",
    description=(
        "Full end-to-end workflow:\n"
        "1. Validates the uploaded image.\n"
        "2. Generates a new Provenance UUID and stores the metadata.\n"
        "3. Injects the watermark payload into the image using the Phase 0 DWT-DCT engine.\n"
        "4. Computes the SHA-256 hash of the final bytes and registers the asset.\n"
        "5. Returns the watermarked lossless PNG.\n\n"
        "The response includes HTTP headers `X-Provenance-UUID` and `X-Asset-SHA256`."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "The watermarked image encoded as a lossless PNG.",
        },
        400: {"description": "Image validation failed."},
        422: {"description": "Request validation failed."},
        500: {"description": "Internal server error during embedding or database operations."},
    }
)
async def embed_watermark_endpoint(
    file: UploadFile = File(...),
    source_type: str = Form("user_upload", description="Type of source, e.g., 'ai_generated' or 'user_upload'"),
    generation_provider: str | None = Form(None, description="Optional provider like 'midjourney'"),
    model_name: str | None = Form(None, description="Optional model name"),
    prompt: str | None = Form(None, description="Optional generation prompt used"),
    db: Session = Depends(get_db),
):
    # 1. Read bytes and ensure filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided in upload."
        )
    
    raw_bytes = await file.read()

    # 2. Validate Image Bytes
    validation_result = validate_image_bytes(raw_bytes, declared_content_type=file.content_type)
    if not validation_result.valid:
        logger.warning(f"Image validation failed: {validation_result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Image validation failed", "errors": validation_result.errors}
        )

    # 3. Create Provenance Record
    prov_data = ProvenanceRecordCreate(
        source_type=source_type,
        generation_provider=generation_provider,
        model_name=model_name,
        prompt=prompt,
    )
    try:
        provenance = create_provenance_record(db, prov_data)
    except Exception as exc:
        logger.error(f"Failed to create provenance record: {exc}")
        raise HTTPException(status_code=500, detail="Database error creating provenance record.")

    # 4. Embed Watermark (CPU intensive Phase 0)
    try:
        watermarked_bytes = embed_watermark_in_bytes(
            image_bytes=raw_bytes,
            provenance_uuid=provenance.provenance_uuid
        )
    except WatermarkServiceError as exc:
        logger.error(f"Watermark embedding failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to embed watermark payload.")
    
    # 5. Register the Asset
    try:
        asset = register_watermarked_asset(
            db=db,
            provenance_record_id=provenance.id,
            image_bytes=watermarked_bytes,
            original_filename=file.filename
        )
    except AssetServiceError as exc:
        logger.error(f"Asset registration failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to register the watermarked asset.")

    # 6. Return the watermarked PNG with metadata headers
    headers = {
        "X-Provenance-UUID": str(provenance.provenance_uuid),
        "X-Asset-SHA256": asset.sha256,
        "Content-Disposition": f'attachment; filename="watermarked_{file.filename}.png"'
    }
    
    return Response(
        content=watermarked_bytes,
        media_type="image/png",
        headers=headers
    )
