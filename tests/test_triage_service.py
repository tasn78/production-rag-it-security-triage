"""
Unit tests for the triage service.

These tests verify that the service correctly coordinates classification,
severity scoring, and evidence retrieval into one structured result.
"""

from dataclasses import dataclass

import pytest

from app.rag.retriever import RetrievalResult
from app.triage.schemas import SeverityLevel, TriageCategory
from app.triage.service import TriageResult, TriageService


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
