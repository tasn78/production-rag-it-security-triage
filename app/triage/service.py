"""
Triage service for combining classification, severity scoring, and retrieval.

This module provides the main application service used to process IT support
tickets and security alerts. It keeps orchestration logic separate from API
routes so the workflow can be tested independently.
"""

from dataclasses import dataclass

from app.rag.retriever import KnowledgeBaseRetriever, RetrievalResult
from app.triage.classifier import classify_ticket
from app.triage.schemas import ClassificationResult, SeverityResult
from app.triage.severity import calculate_severity


@dataclass(frozen=True)
class TriageResult:
    """
    Represents the full structured triage output for a ticket or alert.

    Attributes:
        ticket_text: Original ticket, alert, or issue description.
        classification: Category classification result.
        severity: Severity scoring result.
        retrieved_evidence: Ranked knowledge base chunks relevant to the ticket.
    """

    ticket_text: str
    classification: ClassificationResult
    severity: SeverityResult
    retrieved_evidence: list[RetrievalResult]


class TriageService:
    """
    Application service for processing IT/security triage requests.

    The service coordinates deterministic classification, severity scoring, and
    knowledge base retrieval. It assumes the retriever has already built its
    index before processing requests.
    """

    def __init__(self, retriever: KnowledgeBaseRetriever) -> None:
        """
        Initialize the triage service.

        Args:
            retriever: Built knowledge base retriever used for evidence retrieval.
        """
        self._retriever = retriever

    def triage_ticket(
        self,
        ticket_text: str,
        top_k: int = 3,
    ) -> TriageResult:
        """
        Process a ticket and return structured triage output.

        Args:
            ticket_text: User ticket, security alert, or troubleshooting question.
            top_k: Maximum number of retrieved evidence chunks to return.

        Returns:
            TriageResult containing classification, severity, and evidence.

        Raises:
            ValueError: If ticket_text is empty or top_k is invalid.
            RuntimeError: If the retriever index has not been built.
        """
        classification = classify_ticket(ticket_text)
        severity = calculate_severity(
            ticket_text=ticket_text,
            category=classification.category,
        )
        retrieved_evidence = self._retriever.retrieve(
            query_text=ticket_text,
            top_k=top_k,
        )

        return TriageResult(
            ticket_text=ticket_text,
            classification=classification,
            severity=severity,
            retrieved_evidence=retrieved_evidence,
        )
