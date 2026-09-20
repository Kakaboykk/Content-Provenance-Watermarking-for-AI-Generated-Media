"""
backend/app/api/routes/verify.py

POST /verify

Phase 2B-6: Verification Endpoint.
Accepts an image, attempts to extract the watermark, and returns the verdict and provenance.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.provenance import ProvenanceRecordRead
from app.schemas.verification import VerificationRecordRead
from app.services.verification import verify_image_bytes, VerificationServiceError
from app.services.provenance import get_provenance_record_by_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verify", tags=["Watermark Verification"])


class VerificationResponse(BaseModel):
    match_found: bool
    verdict: str
    provenance_record: ProvenanceRecordRead | None
    verification_record: VerificationRecordRead


@router.post(
    "",
    summary="Verify an image and extract its provenance",
    description=(
        "Accepts an image file and performs blind watermark extraction.\n"
        "Records the attempt in the database and returns the result.\n"
        "Verdicts:\n"
        "- `AUTHENTIC_UNMODIFIED`: Valid watermark and exact file hash match.\n"
        "- `TRACED_BUT_MODIFIED`: Valid watermark found, but file has been altered/compressed.\n"
        "- `NO_WATERMARK_FOUND`: Image contains no recognized watermark payload.\n"
        "- `WATERMARK_UNRECOVERABLE`: Image is too corrupted to decode payload."
    ),
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VerificationResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided in upload."
        )

    raw_bytes = await file.read()

    # Verify bytes and get record
    try:
        ver_record = verify_image_bytes(db, raw_bytes)
    except VerificationServiceError as exc:
        logger.error(f"Verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    prov_record = None
    match_found = False

    if ver_record.extracted_provenance_uuid:
        prov = get_provenance_record_by_uuid(db, ver_record.extracted_provenance_uuid)
        if prov:
            prov_record = prov
            match_found = True

    return VerificationResponse(
        match_found=match_found,
        verdict=ver_record.verdict,
        provenance_record=prov_record,
        verification_record=ver_record,
    )
