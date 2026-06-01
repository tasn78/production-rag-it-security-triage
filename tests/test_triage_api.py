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
from app.triage.summary import TriageSummary


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
            summary=TriageSummary(
                summary_text=(
                    "This ticket was classified as Web Server / Nginx with High Severity."
                ),
                recommended_next_steps=[
                    "Review the top retrieved knowledge-base source: nginx_security.md"
                ],
            ),
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


@dataclass
class FakeHistoryLogger:
    """
    Test double for reading triage request history.
    """

    records: list[dict[str, object]]

    def read_recent(self, limit: int = 10) -> list[dict[str, object]]:
        """
        Return recent fake history records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            Recent fake records.
        """
        if limit < 1:
            raise ValueError("limit must be greater than or equal to 1.")

        return self.records[:limit]


@dataclass
class FakeFeedbackLogger:
    """
    Test double for triage feedback logging.
    """

    records: list[dict[str, object]]

    def log(self, **record: object) -> None:
        """
        Store feedback records in memory for assertions.

        Args:
            record: Feedback summary fields.
        """
        self.records.append(record)

    def summarize(self, recent_limit: int = 10) -> dict[str, object]:
        """
        Return summary statistics for fake feedback records.

        Args:
            recent_limit: Maximum number of recent records to include.

        Returns:
            Feedback summary fields.
        """
        if recent_limit < 1:
            raise ValueError("recent_limit must be greater than or equal to 1.")

        useful_count = sum(1 for record in self.records if record.get("useful") is True)
        total_feedback = len(self.records)
        not_useful_count = total_feedback - useful_count

        useful_percentage = (
            round((useful_count / total_feedback) * 100, 2) if total_feedback > 0 else 0.0
        )

        return {
            "total_feedback": total_feedback,
            "useful_count": useful_count,
            "not_useful_count": not_useful_count,
            "useful_percentage": useful_percentage,
            "recent_feedback": self.records[:recent_limit],
        }


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

        request_id = payload["request_id"]
        assert isinstance(request_id, str)
        assert request_id

        assert payload["category"] == "Web Server / Nginx"
        assert payload["severity"] == "High"
        assert payload["severity_score"] == 5
        assert payload["matched_keywords"] == ["nginx", "401", "429"]
        assert len(payload["retrieved_evidence"]) == 1
        assert payload["retrieved_evidence"][0]["source_name"] == "nginx_security.md"
        assert fake_request_logger.records == [
            {
                "request_id": request_id,
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


def test_triage_history_endpoint_returns_recent_records() -> None:
    """
    Verify that the triage history endpoint returns recent request records.
    """
    original_logger = routes_triage.request_logger
    routes_triage.request_logger = FakeHistoryLogger(
        records=[
            {
                "timestamp_utc": "2026-05-21T00:00:00+00:00",
                "ticket_text": "Nginx logs show repeated 401 responses.",
                "top_k": 3,
                "category": "Web Server / Nginx",
                "severity": "High",
                "severity_score": 5,
                "retrieved_sources": ["nginx_security.md"],
            }
        ]
    )

    try:
        client = TestClient(create_app())

        response = client.get("/triage/history?limit=1")

        assert response.status_code == 200

        payload = response.json()

        assert len(payload["records"]) == 1
        assert payload["records"][0]["category"] == "Web Server / Nginx"
        assert payload["records"][0]["severity"] == "High"
        assert payload["records"][0]["retrieved_sources"] == ["nginx_security.md"]

    finally:
        routes_triage.request_logger = original_logger


def test_triage_history_endpoint_rejects_invalid_limit() -> None:
    """
    Verify that invalid triage history limits are rejected.
    """
    original_logger = routes_triage.request_logger
    routes_triage.request_logger = FakeHistoryLogger(records=[])

    try:
        client = TestClient(create_app())

        response = client.get("/triage/history?limit=0")

        assert response.status_code == 400
        assert response.json()["detail"] == "limit must be greater than or equal to 1."

    finally:
        routes_triage.request_logger = original_logger


def test_triage_feedback_endpoint_records_feedback() -> None:
    """
    Verify that the feedback endpoint records user feedback.
    """
    original_logger = routes_triage.feedback_logger
    fake_logger = FakeFeedbackLogger(records=[])
    routes_triage.feedback_logger = fake_logger

    try:
        client = TestClient(create_app())

        response = client.post(
            "/triage/feedback",
            json={
                "request_id": "test-request-id",
                "ticket_text": "Nginx logs show repeated 401 responses.",
                "category": "Web Server / Nginx",
                "severity": "High",
                "useful": True,
                "notes": "The evidence was helpful.",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"status": "recorded"}

        assert len(fake_logger.records) == 1
        assert fake_logger.records[0]["request_id"] == "test-request-id"
        assert fake_logger.records[0]["ticket_text"] == "Nginx logs show repeated 401 responses."
        assert fake_logger.records[0]["category"] == "Web Server / Nginx"
        assert fake_logger.records[0]["severity"] == "High"
        assert fake_logger.records[0]["useful"] is True
        assert fake_logger.records[0]["notes"] == "The evidence was helpful."

    finally:
        routes_triage.feedback_logger = original_logger


def test_triage_feedback_endpoint_rejects_empty_ticket_text() -> None:
    """
    Verify that empty feedback ticket text is rejected by validation.
    """
    client = TestClient(create_app())

    response = client.post(
        "/triage/feedback",
        json={
            "request_id": "test-request-id",
            "ticket_text": "",
            "category": "Web Server / Nginx",
            "severity": "High",
            "useful": True,
            "notes": "Helpful.",
        },
    )

    assert response.status_code == 422


def test_triage_feedback_summary_endpoint_returns_metrics() -> None:
    """
    Verify that the feedback summary endpoint returns evaluation metrics.
    """
    original_logger = routes_triage.feedback_logger
    routes_triage.feedback_logger = FakeFeedbackLogger(
        records=[
            {
                "timestamp_utc": "2026-05-22T19:44:14+00:00",
                "ticket_text": "Nginx 401 errors.",
                "category": "Security Alert",
                "severity": "High",
                "useful": True,
                "notes": "Helpful evidence.",
            },
            {
                "timestamp_utc": "2026-05-22T19:45:14+00:00",
                "ticket_text": "VPN disconnected.",
                "category": "VPN / Network Access",
                "severity": "Medium",
                "useful": False,
                "notes": "Severity was too low.",
            },
        ]
    )

    try:
        client = TestClient(create_app())

        response = client.get("/triage/feedback/summary?recent_limit=2")

        assert response.status_code == 200

        payload = response.json()

        assert payload["total_feedback"] == 2
        assert payload["useful_count"] == 1
        assert payload["not_useful_count"] == 1
        assert payload["useful_percentage"] == 50.0
        assert len(payload["recent_feedback"]) == 2

    finally:
        routes_triage.feedback_logger = original_logger


def test_triage_feedback_summary_endpoint_rejects_invalid_limit() -> None:
    """
    Verify that invalid feedback summary limits are rejected.
    """
    original_logger = routes_triage.feedback_logger
    routes_triage.feedback_logger = FakeFeedbackLogger(records=[])

    try:
        client = TestClient(create_app())

        response = client.get("/triage/feedback/summary?recent_limit=0")

        assert response.status_code == 400
        assert response.json()["detail"] == ("recent_limit must be greater than or equal to 1.")

    finally:
        routes_triage.feedback_logger = original_logger
