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

def test_query_history_endpoint():
    response = client.get("/api/v1/query/history?session_id=test-session-xyz")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-xyz"
    assert "messages" in data
    assert isinstance(data["messages"], list)

def test_root_endpoints_support():
    # Test root GET /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # Test root GET /documents
    res_docs = client.get("/documents")
    assert res_docs.status_code == 200
    assert "total_documents" in res_docs.json()

    # Test root POST /feedback
    res_fb = client.post("/feedback", json={"query_id": "test-123", "rating": "up"})
    assert res_fb.status_code == 201

def test_ingest_file_upload():
    # Test file upload via multipart/form-data on /ingest
    file_content = b"# Sample Tool\n\nThis is a sample markdown tool reference.\n\n## Syntax\n\n`sample()`"
    files = {"files": ("sample_tool.md", file_content, "text/markdown")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["indexed_documents"] >= 1
    assert data["total_chunks"] >= 1

def test_query_endpoint_validation():
    # Test empty question validation
    response = client.post("/api/v1/query", json={"question": "   "})
    assert response.status_code in [400, 422]

def test_query_endpoint_execution(monkeypatch):
    mock_final_state = {
        "generation": "FastAPI dependency injection uses Depends. [Source: FastAPI Guide > Dependencies]",
        "query_type": "how-to",
        "sources": [{
            "source": "fastapi.md",
            "title": "FastAPI Guide",
            "header_path": "Dependencies",
            "snippet": "Use Depends() to declare dependencies."
        }],
        "retry_count": 0,
        "hallucination_grade": "grounded",
        "execution_steps": ["query_analysis", "retriever", "document_grader", "generator", "hallucination_check"],
    }
    monkeypatch.setattr("src.api.routes.query.rag_app.invoke", lambda state: mock_final_state)

    # Test versioned endpoint
    response = client.post("/api/v1/query", json={"question": "How do I use Depends in FastAPI?"})
    assert response.status_code == 200
    data = response.json()
    assert "query_id" in data
    assert "FastAPI dependency injection" in data["answer"]
    assert data["query_type"] == "how-to"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["title"] == "FastAPI Guide"
    assert data["grounded"] == "grounded"
    assert data["execution_steps"] == mock_final_state["execution_steps"]

    # Test root endpoint /query
    res_root = client.post("/query", json={"question": "How do I use Depends in FastAPI?"})
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert "query_id" in data_root
    assert "FastAPI dependency injection" in data_root["answer"]

def test_download_landing_page():
    # Test GET /download serves HTML portal
    response = client.get("/download")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Download DocuGraph AI" in response.text
    assert "DocuGraphAI_Setup.exe" in response.text

    # Test GET /api/v1/download also serves portal
    res_v1 = client.get("/api/v1/download")
    assert res_v1.status_code == 200

def test_download_info_metadata():
    # Test GET /api/v1/download/info metadata
    response = client.get("/api/v1/download/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "packages" in data

    # Verify windows exe metadata
    exe_info = data["packages"]["exe"]
    assert exe_info["available"] is True
    assert exe_info["size_mb"] > 0
    assert len(exe_info["sha256"]) == 64

    # Verify windows msi metadata
    msi_info = data["packages"]["msi"]
    assert msi_info["available"] is True
    assert msi_info["size_mb"] > 0
    assert len(msi_info["sha256"]) == 64

    # Verify windows zip metadata
    zip_info = data["packages"]["zip"]
    assert zip_info["available"] is True
    assert zip_info["size_mb"] > 0
    assert len(zip_info["sha256"]) == 64

def test_download_binary_headers():
    # Test HEAD/GET for executable download
    response = client.get("/download/exe")
    assert response.status_code == 200
    assert 'attachment; filename="DocuGraphAI_Setup.exe"' in response.headers["content-disposition"]
    assert int(response.headers["content-length"]) > 100_000_000

    # Test GET for MSI download
    res_msi = client.get("/download/msi")
    assert res_msi.status_code == 200
    assert 'attachment; filename="DocuGraphAI_Setup.msi"' in res_msi.headers["content-disposition"]
    assert int(res_msi.headers["content-length"]) > 100_000_000

    # Test GET for ZIP download
    res_zip = client.get("/download/zip")
    assert res_zip.status_code == 200
    assert 'attachment; filename="DocuGraphAI_bundle.zip"' in res_zip.headers["content-disposition"]

    # Test GET for install script
    res_bat = client.get("/download/script")
    assert res_bat.status_code == 200
    assert 'attachment; filename="Install_DocuGraphAI.bat"' in res_bat.headers["content-disposition"]



