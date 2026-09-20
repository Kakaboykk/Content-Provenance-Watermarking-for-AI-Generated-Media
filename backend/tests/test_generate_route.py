"""
backend/tests/test_generate_route.py

Tests for the POST /generate endpoint (Phase 3 Step 2).
"""
import pytest
from fastapi.testclient import TestClient


class TestGenerateEndpoint:
    
    def test_generate_image_success(self, client: TestClient):
        # The endpoint expects a JSON payload containing the prompt
        payload = {"prompt": "A futuristic city at night"}
        
        response = client.post("/generate", json=payload)
        
        assert response.status_code == 200
        
        # Verify headers
        assert "X-AI-Provider" in response.headers
        assert "X-AI-Model" in response.headers
        assert response.headers["Content-Type"] == "image/png"
        
        # Verify content is returned
        image_bytes = response.content
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        
        # Verify it is a decodable image
        import io
        from PIL import Image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
        except Exception as exc:
            pytest.fail(f"Response content is not a valid image: {exc}")

    def test_generate_image_validation_error(self, client: TestClient):
        # Test with missing prompt
        payload = {}
        response = client.post("/generate", json=payload)
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test with empty prompt (assuming min_length=1)
        payload = {"prompt": ""}
        response = client.post("/generate", json=payload)
        assert response.status_code == 422
