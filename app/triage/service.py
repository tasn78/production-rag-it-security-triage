"""
Triage service for combining classification, severity scoring, and retrieval.

This module provides the main application service used to process IT support
tickets and security alerts. It keeps orchestration logic separate from API
routes so the workflow can be tested independently.
"""

from dataclasses import dataclass

from app.config import ML_CATEGORY_MODEL_PATH, USE_ML_CLASSIFIER
from app.ml.category_classifier import MLCategoryClassifier
from app.rag.retriever import KnowledgeBaseRetriever, RetrievalResult
from app.triage.classifier import classify_ticket
from app.triage.schemas import ClassificationResult, SeverityResult
from app.triage.severity import calculate_severity
from app.triage.summary import TriageSummary, generate_triage_summary


@dataclass(frozen=True)
class TriageResult:
    """
    Represents the full structured triage output for a ticket or alert.

    Attributes:
        ticket_text: Original ticket, alert, or issue description.
        classification: Category classification result.
        severity: Severity scoring result.
        retrieved_evidence: Ranked knowledge base chunks relevant to the ticket.
        summary: Generated triage summary and recommended next steps.
    """

    ticket_text: str
    classification: ClassificationResult
    severity: SeverityResult
    retrieved_evidence: list[RetrievalResult]
    summary: TriageSummary


class TriageService:
    """
    Application service for processing IT/security triage requests.

    The service coordinates deterministic classification, severity scoring, and
    knowledge base retrieval. It assumes the retriever has already built its
    index before processing requests.
    """

    def __init__(
        self,
        retriever: KnowledgeBaseRetriever,
        ml_classifier: MLCategoryClassifier | None = None,
    ) -> None:
        """
        Initialize the triage service.

        Args:
            retriever: Built knowledge base retriever used for evidence retrieval.
            ml_classifier: Optional ML classifier used for category prediction.
        """
        self._retriever = retriever
        self._ml_classifier = ml_classifier or self._build_ml_classifier()

    def _build_ml_classifier(self) -> MLCategoryClassifier | None:
        """
        Build and load the optional ML classifier when enabled.

        Returns:
            Loaded ML classifier when enabled and available, otherwise None.
        """
        if not USE_ML_CLASSIFIER:
            return None

        classifier = MLCategoryClassifier(model_path=ML_CATEGORY_MODEL_PATH)

        try:
            classifier.load()
        except (FileNotFoundError, OSError, ValueError):
            return None

        return classifier

    def _classify_ticket(self, ticket_text: str) -> ClassificationResult:
        """
        Classify a ticket using ML when available, otherwise rule-based logic.

        Args:
            ticket_text: Raw ticket, alert, or issue description.

        Returns:
            ClassificationResult from ML or rule-based classification.
        """
        if self._ml_classifier is not None and self._ml_classifier.is_available:
            try:
                return self._ml_classifier.predict(ticket_text)
            except (RuntimeError, ValueError):
                pass

        return classify_ticket(ticket_text)

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
        classification = self._classify_ticket(ticket_text)
        severity = calculate_severity(
            ticket_text=ticket_text,
            category=classification.category,
        )
        retrieved_evidence = self._retriever.retrieve(
            query_text=ticket_text,
            top_k=top_k,
        )
        summary = generate_triage_summary(
            ticket_text=ticket_text,
            category=classification.category,
            severity=severity,
            retrieved_evidence=retrieved_evidence,
        )

        return TriageResult(
            ticket_text=ticket_text,
            classification=classification,
            severity=severity,
            retrieved_evidence=retrieved_evidence,
            summary=summary,
        )
