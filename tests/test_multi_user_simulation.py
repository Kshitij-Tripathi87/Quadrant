import pytest
import uuid
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestMultiUserScenarios:
    """
    Simulates real-world user personas interacting with the
    Technical Documentation Assistant API.
    """

    def test_user_backend_engineer_fastapi(self):
        """User 1: Backend Engineer inquiring about FastAPI dependency injection lifecycle."""
        session_id = f"user-backend-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I implement dependency injection with cleanup in FastAPI using yield?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "yield" in data["answer"].lower() or "dependencies" in data["answer"].lower()
        assert data["query_type"] in ["how-to", "conceptual"]
        assert len(data["sources"]) > 0
        assert data["grounded"] == "grounded"
        assert "generator" in data["execution_steps"]
        assert data["session_id"] == session_id

    def test_user_ml_engineer_langgraph(self):
        """User 2: ML/AI Engineer asking about LangGraph StateGraph conditional edges."""
        session_id = f"user-ml-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do conditional edges work in LangGraph StateGraph?",
            "session_id": session_id,
        }
        response = client.post("/query", json=payload)  # Root path endpoint
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert len(data["answer"]) > 50
        assert len(data["sources"]) > 0
        assert data["grounded"] == "grounded"
        assert any("langgraph" in s["source"].lower() or "langgraph" in s["title"].lower() for s in data["sources"])

    def test_user_api_developer_pydantic(self):
        """User 3: API Developer asking about Pydantic v2 field_validator."""
        session_id = f"user-pydantic-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I use @field_validator in Pydantic v2 to validate an attribute?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "validator" in data["answer"].lower() or "pydantic" in data["answer"].lower()
        assert len(data["sources"]) > 0
        assert data["grounded"] == "grounded"

    def test_user_architect_rest_principles(self):
        """User 4: Systems Architect asking about REST HTTP method idempotency."""
        session_id = f"user-arch-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "What is the difference between safe and idempotent HTTP methods in REST?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "idempotent" in data["answer"].lower() or "put" in data["answer"].lower()
        assert len(data["sources"]) > 0

    def test_user_ambiguous_query_triggering_correction(self):
        """User 5: Novice developer submitting an abbreviated query."""
        session_id = f"user-novice-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I manage state in StateGraph?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "state" in data["answer"].lower()
        assert len(data["sources"]) > 0

    def test_user_out_of_scope_query_fallback(self):
        """User 6: Developer asking about out-of-scope technology triggering self-correction / fallback."""
        session_id = f"user-out-of-scope-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I set up a Kubernetes ingress controller with cert-manager TLS?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        # The system either executes web search fallback or gracefully states context is insufficient
        assert len(data["answer"]) > 10
        assert data["retries_used"] <= 2
        assert "execution_steps" in data

    def test_user_multi_turn_session_memory(self):
        """User 7: User performing a multi-turn conversation and inspecting session history."""
        session_id = f"session-conversation-{uuid.uuid4().hex[:8]}"

        # Turn 1
        res1 = client.post("/api/v1/query", json={
            "question": "What is the primary function of FastAPI Depends?",
            "session_id": session_id,
        })
        assert res1.status_code == 200
        q1_id = res1.json()["query_id"]

        # Turn 2
        res2 = client.post("/api/v1/query", json={
            "question": "How do I test FastAPI endpoints with TestClient?",
            "session_id": session_id,
        })
        assert res2.status_code == 200

        # Retrieve History
        hist_res = client.get(f"/api/v1/query/history?session_id={session_id}")
        assert hist_res.status_code == 200
        history_data = hist_res.json()
        assert history_data["session_id"] == session_id
        assert history_data["total_messages"] >= 2
        assert any(q1_id == msg["id"] for msg in history_data["messages"])

    def test_user_feedback_evaluation_flow(self):
        """User 8: User submitting evaluation feedback on an answer."""
        session_id = f"session-feedback-{uuid.uuid4().hex[:6]}"
        query_res = client.post("/api/v1/query", json={
            "question": "What are REST API status codes for success?",
            "session_id": session_id,
        })
        assert query_res.status_code == 200
        q_id = query_res.json()["query_id"]

        # Thumbs up feedback
        fb_up = client.post("/feedback", json={
            "query_id": q_id,
            "rating": "up",
            "comment": "Very accurate, included 200 and 201."
        })
        assert fb_up.status_code == 201
        assert fb_up.json()["status"] == "recorded"

        # Thumbs down feedback
        fb_down = client.post("/api/v1/feedback", json={
            "query_id": q_id,
            "rating": "down",
            "comment": "Could provide more examples."
        })
        assert fb_down.status_code == 201
        assert fb_down.json()["status"] == "recorded"

    def test_admin_corpus_catalog(self):
        """User 9: Documentation Admin viewing indexed corpus catalog."""
        docs_res = client.get("/api/v1/documents")
        assert docs_res.status_code == 200
        docs_data = docs_res.json()
        assert docs_data["total_documents"] >= 4
        assert docs_data["total_vectors"] >= 20

        # Verify that expected foundational documents are listed
        sources = [d["source"] for d in docs_data["documents"]]
        assert any("fastapi" in s.lower() for s in sources)
        assert any("langgraph" in s.lower() for s in sources)
        assert any("pydantic" in s.lower() for s in sources)

    def test_user_document_ingestion_and_followup_query(self):
        """User 10: Ingesting a new custom technical guide and querying it."""
        custom_content = (
            "# Custom Cache System Guide\n\n"
            "## Two-Tier Cache Architecture\n\n"
            "The system uses an L1 in-memory LRU cache and an L2 Redis distributed cache.\n"
            "Cache invalidation occurs via TTL expiration or explicit purge commands.\n"
        ).encode("utf-8")

        files = {"files": ("custom_cache_guide.md", custom_content, "text/markdown")}
        ingest_res = client.post("/ingest", files=files)
        assert ingest_res.status_code == 201
        ingest_data = ingest_res.json()
        assert ingest_data["status"] == "success"
        assert ingest_data["total_chunks"] >= 1
