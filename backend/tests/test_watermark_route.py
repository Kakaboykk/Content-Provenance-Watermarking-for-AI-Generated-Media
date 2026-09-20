"""
backend/tests/test_watermark_route.py

Tests for the POST /watermark/embed endpoint (Phase 2B-5).
Ensures the complete E2E flow works correctly.
"""
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.models.provenance import ProvenanceRecord
from app.models.asset import WatermarkedAsset


def _make_dummy_image(width=64, height=64) -> bytes:
    img = Image.new("RGB", (width, height), color=(150, 100, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class TestWatermarkEmbedEndpoint:

    def test_successful_embedding(self, client: TestClient, db_session):
        img_bytes = _make_dummy_image(256, 256)
        
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        data = {
            "source_type": "ai_generated",
            "generation_provider": "pytest",
        }
        
        response = client.post("/watermark/embed", files=files, data=data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        
        # Verify Headers
        prov_uuid = response.headers.get("X-Provenance-UUID")
        asset_sha = response.headers.get("X-Asset-SHA256")
        
        assert prov_uuid is not None
        assert asset_sha is not None
        
        # Verify database insertion
        prov_record = db_session.query(ProvenanceRecord).filter_by(provenance_uuid=uuid.UUID(prov_uuid)).first()
        assert prov_record is not None
        assert prov_record.source_type == "ai_generated"
        assert prov_record.generation_provider == "pytest"
        
        asset_record = db_session.query(WatermarkedAsset).filter_by(sha256=asset_sha).first()
        assert asset_record is not None
        assert asset_record.provenance_record_id == prov_record.id
        
        # The returned bytes should match the SHA256 exactly
        import hashlib
        assert hashlib.sha256(response.content).hexdigest() == asset_sha

    def test_validation_failure_returns_400(self, client: TestClient):
        # 32x32 is too small (MIN_DIMENSION = 64)
        img_bytes = _make_dummy_image(32, 32)
        
        files = {"file": ("small.jpg", img_bytes, "image/jpeg")}
        data = {"source_type": "user_upload"}
        
        response = client.post("/watermark/embed", files=files, data=data)
        
        assert response.status_code == 400
        json_data = response.json()
        assert "validation failed" in json_data["detail"]["message"].lower()
        assert len(json_data["detail"]["errors"]) > 0

    def test_missing_file_returns_422(self, client: TestClient):
        data = {"source_type": "user_upload"}
        
        response = client.post("/watermark/embed", data=data)
        assert response.status_code == 422
