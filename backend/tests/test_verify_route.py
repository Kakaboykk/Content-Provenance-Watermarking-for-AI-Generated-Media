"""
backend/tests/test_verify_route.py

Tests for the POST /verify endpoint (Phase 2B-6).
"""
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.services.watermark import embed_watermark_in_bytes
from app.services.asset import register_watermarked_asset
from app.models.provenance import ProvenanceRecord
from app.schemas.provenance import ProvenanceRecordCreate
from app.services.provenance import create_provenance_record


def _make_dummy_image(width=512, height=512) -> bytes:
    img = Image.new("RGB", (width, height), color=(50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class TestVerifyEndpoint:

    def test_authentic_unmodified(self, client: TestClient, db_session):
        # 1. Setup DB state
        prov = create_provenance_record(db_session, ProvenanceRecordCreate(source_type="pytest"))
        raw_bytes = _make_dummy_image()
        watermarked_bytes = embed_watermark_in_bytes(raw_bytes, prov.provenance_uuid)
        register_watermarked_asset(db_session, prov.id, watermarked_bytes)

        # 2. Call Verify endpoint with the exact bytes
        files = {"file": ("watermarked.png", watermarked_bytes, "image/png")}
        response = client.post("/verify", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["verdict"] == "AUTHENTIC_UNMODIFIED"
        assert data["match_found"] is True
        assert data["provenance_record"]["provenance_uuid"] == str(prov.provenance_uuid)

    def test_traced_but_modified(self, client: TestClient, db_session):
        # 1. Setup DB state
        prov = create_provenance_record(db_session, ProvenanceRecordCreate(source_type="pytest"))
        raw_bytes = _make_dummy_image()
        watermarked_bytes = embed_watermark_in_bytes(raw_bytes, prov.provenance_uuid)
        
        # Do NOT register the asset, OR alter the image so the SHA-256 changes
        # Let's alter the image by opening and saving it as JPEG
        img = Image.open(io.BytesIO(watermarked_bytes))
        altered_buf = io.BytesIO()
        img.save(altered_buf, format="JPEG", quality=95)
        altered_bytes = altered_buf.getvalue()
        
        # Register the original bytes
        register_watermarked_asset(db_session, prov.id, watermarked_bytes)

        # 2. Call Verify endpoint with the ALTERED bytes
        files = {"file": ("altered.jpg", altered_bytes, "image/jpeg")}
        response = client.post("/verify", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Watermark survived JPEG compression, but SHA256 doesn't match
        assert data["verdict"] == "TRACED_BUT_MODIFIED"
        assert data["match_found"] is True
        assert data["provenance_record"]["provenance_uuid"] == str(prov.provenance_uuid)

    def test_no_watermark_found(self, client: TestClient):
        # 1. Call Verify endpoint with a clean image
        clean_bytes = _make_dummy_image()
        files = {"file": ("clean.jpg", clean_bytes, "image/jpeg")}
        response = client.post("/verify", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["verdict"] == "NO_WATERMARK_FOUND"
        assert data["match_found"] is False
        assert data["provenance_record"] is None
        assert data["verification_record"]["verdict"] == "NO_WATERMARK_FOUND"
