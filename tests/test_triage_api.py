"""
Unit tests for the FastAPI triage endpoint.

These tests override the route-level service provider so the API can be tested
without loading a real embedding model or FAISS index.
"""

from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api import routes_triage
from app.main import create_app
from app.rag.retriever import RetrievalResult
from app.triage.schemas import (
    ClassificationResult,
    SeverityLevel,
    SeverityResult,
    TriageCategory,
)
from app.triage.service import TriageResult


@dataclass
class FakeTriageService:
    """
    Test double for TriageService.

    This fake service returns deterministic triage output for API tests without
    invoking embeddings, vector search, or document loading.
    """

    def triage_ticket(self, ticket_text: str, top_k: int = 3) -> TriageResult:
        """
        Return deterministic triage output for an API request.

        Args:
            ticket_text: Ticket text from the API request.
            top_k: Maximum number of retrieved evidence chunks.

        Returns:
            Structured fake triage result.
        """
        return TriageResult(
            ticket_text=ticket_text,
            classification=ClassificationResult(
                category=TriageCategory.WEB_SERVER,
                matched_keywords=["nginx", "401", "429"],
            ),
            severity=SeverityResult(
                severity=SeverityLevel.HIGH,
                score=5,
                reasons=["Web server issue may affect service availability."],
            ),
            retrieved_evidence=[
                RetrievalResult(
                    source_name="nginx_security.md",
                    chunk_index=0,
                    text="Nginx evidence chunk.",
                    score=0.95,
                    rank=1,
                )
            ][:top_k],
        )


class FakeServiceProvider:
    """
    Test service provider that returns a fake triage service.
    """

    def get_service(self) -> FakeTriageService:
        """
        Return the fake triage service.

        Returns:
            FakeTriageService instance.
        """
        return FakeTriageService()


@dataclass
class FakeRequestLogger:
    """
    Test double for request logging.
    """

    records: list[dict[str, object]]

    def log(self, **record: object) -> None:
        """
        Store log records in memory for assertions.

        Args:
            record: Triage request summary fields.
        """
        self.records.append(record)


def test_health_check_returns_ok() -> None:
    """
    Verify that the health check endpoint returns application status.
    """
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Production RAG System for IT and Security Triage",
        "version": "0.1.0",
    }


def test_triage_endpoint_returns_structured_result() -> None:
    """
    Verify that the triage endpoint returns category, severity, and evidence.
    """
    original_provider = routes_triage.service_provider
    original_request_logger = routes_triage.request_logger
    fake_request_logger = FakeRequestLogger(records=[])

    routes_triage.service_provider = FakeServiceProvider()
    routes_triage.request_logger = fake_request_logger

    try:
        client = TestClient(create_app())

        response = client.post(
            "/triage",
            json={
                "ticket_text": "Nginx logs show repeated 401 and 429 responses.",
                "top_k": 1,
            },
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["category"] == "Web Server / Nginx"
        assert payload["severity"] == "High"
        assert payload["severity_score"] == 5
        assert payload["matched_keywords"] == ["nginx", "401", "429"]
        assert len(payload["retrieved_evidence"]) == 1
        assert payload["retrieved_evidence"][0]["source_name"] == "nginx_security.md"
        assert fake_request_logger.records == [
            {
                "ticket_text": "Nginx logs show repeated 401 and 429 responses.",
                "top_k": 1,
                "category": "Web Server / Nginx",
                "severity": "High",
                "severity_score": 5,
                "retrieved_sources": ["nginx_security.md"],
            }
        ]

    finally:
        routes_triage.service_provider = original_provider
        routes_triage.request_logger = original_request_logger


def test_triage_endpoint_rejects_empty_ticket_text() -> None:
    """
    Verify that empty ticket text is rejected by request validation.
    """
    client = TestClient(create_app())

    response = client.post(
        "/triage",
        json={
            "ticket_text": "",
            "top_k": 1,
        },
    )

    assert response.status_code == 422


def test_triage_endpoint_rejects_invalid_top_k() -> None:
    """
    Verify that invalid top_k values are rejected by request validation.
    """
    client = TestClient(create_app())

    response = client.post(
        "/triage",
        json={
            "ticket_text": "Nginx 401 errors",
            "top_k": 0,
        },
    )

    assert response.status_code == 422
