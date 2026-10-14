import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data
    assert data["vector_store_count"] >= 0

def test_get_documents_endpoint():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_feedback_submission():
    payload = {
        "query_id": "test-uuid-123",
        "rating": "up",
        "comment": "Accurate explanation with code."
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "recorded"
    assert "feedback_id" in data

def test_feedback_invalid_rating():
    payload = {
        "query_id": "test-uuid-123",
        "rating": "invalid_score"
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code in [400, 422]

def test_ingest_empty_urls():
    payload = {"urls": []}
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code in [400, 422]
