import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
import httpx
from httpx import ASGITransport

from src.api.main import app

client = TestClient(app)

class TestDocuSignIntegration:
    """
    Verifies domain-specific DocuSign technical documentation retrieval,
    answer accuracy, code citation grounding, and concurrent user scaling.
    """

    def test_docusign_envelope_creation_query(self):
        """User asking about creating an envelope with Python SDK."""
        session_id = f"test-docusign-env-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I create and send an envelope using the DocuSign Python SDK?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "envelope" in data["answer"].lower()
        assert len(data["sources"]) > 0
        assert any("docusign" in s["source"].lower() or "docusign" in s["title"].lower() for s in data["sources"])
        assert data["grounded"] in ["grounded", "extractive_offline_fallback"]

    def test_docusign_jwt_oauth_query(self):
        """User asking about DocuSign JWT OAuth grant authentication."""
        session_id = f"test-docusign-jwt-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How does DocuSign OAuth 2.0 JWT Grant authentication work with RSA private keys?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "jwt" in data["answer"].lower() or "token" in data["answer"].lower() or "rsa" in data["answer"].lower()
        assert len(data["sources"]) > 0
        assert any("jwt" in s["source"].lower() or "oauth" in s["source"].lower() for s in data["sources"])

    def test_docusign_embedded_signing_query(self):
        """User asking about embedded in-app signing and clientUserId."""
        session_id = f"test-docusign-embed-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I configure embedded signing using recipient view and clientUserId in DocuSign?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "client" in data["answer"].lower() or "url" in data["answer"].lower() or "signing" in data["answer"].lower()
        assert len(data["sources"]) > 0

    def test_docusign_webhook_hmac_query(self):
        """User asking about DocuSign Connect webhook HMAC SHA-256 verification."""
        session_id = f"test-docusign-hmac-{uuid.uuid4().hex[:6]}"
        payload = {
            "question": "How do I verify DocuSign Connect webhook HMAC SHA-256 signatures in Python?",
            "session_id": session_id,
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()

        assert "hmac" in data["answer"].lower() or "signature" in data["answer"].lower() or "sha" in data["answer"].lower()
        assert len(data["sources"]) > 0

    @pytest.mark.asyncio
    async def test_concurrent_docusign_user_scaling(self):
        """Simulates 20 concurrent users querying DocuSign endpoints simultaneously."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            tasks = []
            for i in range(20):
                payload = {
                    "question": "How do I create and send an envelope using the DocuSign Python SDK?",
                    "session_id": f"concurrent-sess-{i:02d}-{uuid.uuid4().hex[:4]}",
                }
                tasks.append(async_client.post("/api/v1/query", json=payload, timeout=60.0))

            responses = await asyncio.gather(*tasks)

            # All 20 concurrent requests must complete with 200 OK
            assert all(r.status_code == 200 for r in responses), "Not all concurrent requests succeeded"
            for r in responses:
                d = r.json()
                assert len(d["answer"]) > 50
                assert len(d["sources"]) > 0
