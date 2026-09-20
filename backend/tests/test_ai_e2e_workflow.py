"""
backend/tests/test_ai_e2e_workflow.py

Tests for Phase 3 Step 3: End-to-End AI Integration.
Ensures that an AI-generated image can successfully traverse:
/generate -> /watermark/embed -> /verify
"""
import io
import pytest
from fastapi.testclient import TestClient

class TestAIE2EWorkflow:
    def test_ai_generation_to_verification_flow(self, client: TestClient, db_session):
        # ---------------------------------------------------------
        # 1. Generate AI Image
        # ---------------------------------------------------------
        prompt = "A majestic cyberpunk cityscape at sunset"
        gen_payload = {"prompt": prompt}
        
        gen_resp = client.post("/generate", json=gen_payload)
        assert gen_resp.status_code == 200, f"Generation failed: {gen_resp.text}"
        
        provider = gen_resp.headers.get("X-AI-Provider")
        model = gen_resp.headers.get("X-AI-Model")
        
        assert provider is not None
        assert model is not None
        
        raw_image_bytes = gen_resp.content
        assert len(raw_image_bytes) > 0
        
        # ---------------------------------------------------------
        # 2. Embed Watermark and Register Provenance
        # ---------------------------------------------------------
        embed_data = {
            "source_type": "ai_generated",
            "generation_provider": provider,
            "model_name": model,
            "prompt": prompt,
        }
        embed_files = {
            "file": ("ai_generated.png", raw_image_bytes, "image/png")
        }
        
        embed_resp = client.post("/watermark/embed", data=embed_data, files=embed_files)
        assert embed_resp.status_code == 200, f"Embedding failed: {embed_resp.text}"
        
        provenance_uuid = embed_resp.headers.get("X-Provenance-UUID")
        asset_sha256 = embed_resp.headers.get("X-Asset-SHA256")
        
        assert provenance_uuid is not None
        assert asset_sha256 is not None
        
        watermarked_bytes = embed_resp.content
        
        # ---------------------------------------------------------
        # 3. Verify Watermarked Image
        # ---------------------------------------------------------
        verify_files = {
            "file": ("protected_image.png", watermarked_bytes, "image/png")
        }
        verify_resp = client.post("/verify", files=verify_files)
        assert verify_resp.status_code == 200, f"Verification failed: {verify_resp.text}"
        
        verify_data = verify_resp.json()
        assert verify_data["verdict"] == "AUTHENTIC_UNMODIFIED"
        assert verify_data["match_found"] is True
        
        # Verify that the provenance metadata was perfectly preserved through the loop
        prov_record = verify_data["provenance_record"]
        assert prov_record["provenance_uuid"] == provenance_uuid
        assert prov_record["source_type"] == "ai_generated"
        assert prov_record["generation_provider"] == provider
        assert prov_record["model_name"] == model
        assert prov_record["prompt"] == prompt
