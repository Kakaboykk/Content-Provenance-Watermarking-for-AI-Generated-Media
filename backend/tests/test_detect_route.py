"""
backend/tests/test_detect_route.py

Tests for the POST /detect-ai endpoint.
"""
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

class TestDetectAIEndpoint:
    
    def test_detect_ai_success_ai_generated(self, client: TestClient):
        # We need an image size % 3 == 0 to get AI_GENERATED from the mock detector.
        # Let's generate a valid PNG image and pad it until its byte length is a multiple of 3.
        img = Image.new("RGB", (64, 64))
        out = io.BytesIO()
        img.save(out, format="PNG")
        image_bytes = out.getvalue()
        
        while len(image_bytes) % 3 != 0:
            image_bytes += b"\x00"
            
        files = {"file": ("test.png", image_bytes, "image/png")}
        response = client.post("/detect-ai", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "AI_GENERATED"
        assert data["confidence"] == 0.95
        assert data["provider"] == "mock"

    def test_detect_ai_success_likely_human(self, client: TestClient):
        img = Image.new("RGB", (64, 64))
        out = io.BytesIO()
        img.save(out, format="PNG")
        image_bytes = out.getvalue()
        
        while len(image_bytes) % 3 != 1:
            image_bytes += b"\x00"
            
        files = {"file": ("test.png", image_bytes, "image/png")}
        response = client.post("/detect-ai", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "LIKELY_HUMAN"
        assert data["confidence"] == 0.92

    def test_detect_ai_success_uncertain(self, client: TestClient):
        img = Image.new("RGB", (64, 64))
        out = io.BytesIO()
        img.save(out, format="PNG")
        image_bytes = out.getvalue()
        
        while len(image_bytes) % 3 != 2:
            image_bytes += b"\x00"
            
        files = {"file": ("test.png", image_bytes, "image/png")}
        response = client.post("/detect-ai", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "UNCERTAIN"
        assert data["confidence"] == 0.55

    def test_detect_ai_missing_file(self, client: TestClient):
        response = client.post("/detect-ai")
        assert response.status_code == 422

    def test_detect_ai_invalid_image_format(self, client: TestClient):
        # A file that is not a valid image
        files = {"file": ("test.txt", b"Hello, world!", "text/plain")}
        response = client.post("/detect-ai", files=files)
        
        # Depends on exactly how the validation throws, usually 400
        assert response.status_code == 400
        assert "validation failed" in response.json()["detail"].lower()

    def test_detect_ai_empty_file(self, client: TestClient):
        files = {"file": ("test.png", b"", "image/png")}
        response = client.post("/detect-ai", files=files)
        assert response.status_code == 400
