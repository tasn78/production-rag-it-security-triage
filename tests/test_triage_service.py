"""
Unit tests for the triage service.

These tests verify that the service correctly coordinates classification,
severity scoring, and evidence retrieval into one structured result.
"""

from dataclasses import dataclass

import pytest

from app.rag.retriever import RetrievalResult
from app.triage.schemas import ClassificationResult, ClassifierMode, SeverityLevel, TriageCategory
from app.triage.service import TriageResult, TriageService


class FakeAvailableMLClassifier:
    """
    Fake available ML classifier for testing service integration.
    """

    @property
    def is_available(self) -> bool:
        """
        Return that the fake ML classifier is available.
        """
        return True

    def predict(self, ticket_text: str) -> ClassificationResult:
        """
        Return a deterministic ML classification.
        """
        return ClassificationResult(
            category=TriageCategory.SHARED_DRIVE_ACCESS,
            matched_keywords=[],
        )


class FakeFailingMLClassifier:
    """
    Fake ML classifier that fails during prediction.
    """

    @property
    def is_available(self) -> bool:
        """
        Return that the fake ML classifier is available.
        """
        return True

    def predict(self, ticket_text: str) -> ClassificationResult:
        """
        Raise an error to verify rule-based fallback.
        """
        raise RuntimeError("model failure")


@dataclass
class FakeRetriever:
    """
    Test double for KnowledgeBaseRetriever.

    This fake retriever avoids loading embeddings or FAISS while allowing the
    triage service orchestration logic to be tested directly.
    """

    is_ready: bool = True

    def retrieve(self, query_text: str, top_k: int = 3) -> list[RetrievalResult]:
        """
        Return deterministic retrieval results for service tests.

        Args:
            query_text: Ticket text to retrieve evidence for.
            top_k: Maximum number of results to return.

        Returns:
            List of fake RetrievalResult objects.

        Raises:
            RuntimeError: If the fake retriever is marked as not ready.
            ValueError: If top_k is invalid.
        """
        if not self.is_ready:
            raise RuntimeError("retriever index has not been built")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        return [
            RetrievalResult(
                source_name="nginx_security.md",
                chunk_index=0,
                text=f"Retrieved evidence for: {query_text}",
                score=0.95,
                rank=1,
            )
        ][:top_k]


def test_triage_service_returns_structured_security_result() -> None:
    """
    Verify that security alert text produces category, severity, and evidence.
    """
    service = TriageService(retriever=FakeRetriever())

    result = service.triage_ticket(
        ticket_text=(
            "Repeated failed login attempts from an external IP indicate brute force activity."
        ),
        top_k=1,
    )

    assert isinstance(result, TriageResult)
    assert result.classification.category == TriageCategory.SECURITY_ALERT
    assert result.classifier_mode == ClassifierMode.RULE_BASED
    assert result.severity.severity in {SeverityLevel.HIGH, SeverityLevel.CRITICAL}
    assert len(result.retrieved_evidence) == 1
    assert result.retrieved_evidence[0].source_name == "nginx_security.md"


def test_triage_service_returns_structured_vpn_result() -> None:
    """
    Verify that VPN issue text produces the expected category and evidence.
    """
    service = TriageService(retriever=FakeRetriever())

    result = service.triage_ticket(
        ticket_text="User connects to VPN but cannot access internal resources.",
        top_k=1,
    )

    assert result.classification.category == TriageCategory.VPN_NETWORK_ACCESS
    assert result.severity.severity in {SeverityLevel.LOW, SeverityLevel.MEDIUM}
    assert len(result.retrieved_evidence) == 1


def test_triage_service_rejects_empty_ticket_text() -> None:
    """
    Verify that empty ticket text is rejected by the service workflow.
    """
    service = TriageService(retriever=FakeRetriever())

    with pytest.raises(ValueError, match="ticket_text cannot be empty"):
        service.triage_ticket(ticket_text="   ", top_k=1)


def test_triage_service_rejects_invalid_top_k() -> None:
    """
    Verify that invalid retrieval count values are rejected.
    """
    service = TriageService(retriever=FakeRetriever())

    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        service.triage_ticket(ticket_text="Nginx 401 errors", top_k=0)


def test_triage_service_requires_ready_retriever() -> None:
    """
    Verify that the service fails if the retriever index has not been built.
    """
    service = TriageService(retriever=FakeRetriever(is_ready=False))

    with pytest.raises(RuntimeError, match="retriever index has not been built"):
        service.triage_ticket(ticket_text="Nginx 401 errors", top_k=1)


def test_triage_service_uses_injected_ml_classifier_when_available() -> None:
    """
    Verify that the triage service uses an injected available ML classifier.
    """
    retriever = FakeRetriever()
    service = TriageService(
        retriever=retriever,
        ml_classifier=FakeAvailableMLClassifier(),
    )

    result = service.triage_ticket(
        ticket_text="Nginx logs show repeated HTTP 429 responses.",
        top_k=1,
    )

    assert result.classification.category == TriageCategory.SHARED_DRIVE_ACCESS
    assert result.classification.matched_keywords == []
    assert result.classifier_mode == ClassifierMode.ML


def test_triage_service_falls_back_to_rules_when_ml_classifier_fails() -> None:
    """
    Verify that the triage service falls back to rule-based classification.
    """
    retriever = FakeRetriever()
    service = TriageService(
        retriever=retriever,
        ml_classifier=FakeFailingMLClassifier(),
    )

    result = service.triage_ticket(
        ticket_text="Nginx logs show repeated 401 and 429 responses.",
        top_k=1,
    )

    assert result.classification.category == TriageCategory.WEB_SERVER
    assert "nginx" in result.classification.matched_keywords
    assert result.classifier_mode == ClassifierMode.ML_FALLBACK_RULE_BASED
