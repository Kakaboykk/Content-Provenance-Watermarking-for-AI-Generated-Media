"""
Tests for GET /health endpoint.
"""


def test_health_returns_ok(client):
    """The health endpoint must return status=ok with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # database field is present (may be 'ok' or 'unreachable' depending on test env)
    assert "database" in data


def test_health_content_type(client):
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


def test_docs_accessible(client):
    """Swagger UI must be accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json_accessible(client):
    """OpenAPI schema must be served."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Content Provenance Watermarking API"
    assert "/health" in schema["paths"]
