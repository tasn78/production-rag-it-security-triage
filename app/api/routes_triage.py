"""
FastAPI routes for IT and security triage.

This module exposes API endpoints for submitting tickets or alerts and receiving
structured triage output, including category, severity, and retrieved evidence.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.retriever import KnowledgeBaseRetriever
from app.triage.feedback_logger import TriageFeedbackLogger
from app.triage.request_logger import TriageRequestLogger
from app.triage.service import TriageService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_DIRECTORY = PROJECT_ROOT / "data" / "docs"

DEFAULT_LOG_FILE_PATH = PROJECT_ROOT / "data" / "log" / "triage_requests.jsonl"
DEFAULT_FEEDBACK_LOG_FILE_PATH = PROJECT_ROOT / "data" / "log" / "triage_feedback.jsonl"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triage", tags=["triage"])


class TriageRequest(BaseModel):
    """
    API request body for triage requests.

    Attributes:
        ticket_text: User ticket, security alert, or troubleshooting question.
        top_k: Maximum number of retrieved evidence chunks to return.
    """

    ticket_text: str = Field(
        ...,
        min_length=1,
        description="Ticket, alert, or issue description to triage.",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of evidence chunks to retrieve.",
    )


class RetrievedEvidenceResponse(BaseModel):
    """
    API response model for retrieved knowledge base evidence.

    Attributes:
        source_name: Name of the source document.
        chunk_index: Chunk index within the source document.
        text: Retrieved evidence text.
        score: Similarity score.
        rank: One-based retrieval rank.
    """

    source_name: str
    chunk_index: int
    text: str
    score: float
    rank: int


class TriageResponse(BaseModel):
    """
    API response body for triage results.

    Attributes:
        ticket_text: Original ticket, alert, or issue description.
        category: Assigned triage category.
        matched_keywords: Keywords that contributed to classification.
        severity: Assigned severity label.
        severity_score: Numeric severity score.
        severity_reasons: Human-readable reasons contributing to severity.
        retrieved_evidence: Ranked evidence chunks from the knowledge base.
    """

    ticket_text: str
    category: str
    matched_keywords: list[str]
    severity: str
    severity_score: int
    severity_reasons: list[str]
    retrieved_evidence: list[RetrievedEvidenceResponse]


class TriageHistoryResponse(BaseModel):
    """
    API response body for recent triage request history.

    Attributes:
        records: Recent triage request log records.
    """

    records: list[dict[str, object]]


class TriageFeedbackRequest(BaseModel):
    """
    API request body for triage feedback.

    Attributes:
        ticket_text: Original ticket, alert, or issue description.
        category: Category assigned by the triage system.
        severity: Severity assigned by the triage system.
        useful: Whether the user found the triage result useful.
        notes: Optional feedback notes.
    """

    ticket_text: str = Field(
        ...,
        min_length=1,
        description="Original ticket, alert, or issue description.",
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Category assigned by the triage system.",
    )
    severity: str = Field(
        ...,
        min_length=1,
        description="Severity assigned by the triage system.",
    )
    useful: bool = Field(
        ...,
        description="Whether the user found the triage result useful.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional feedback notes.",
    )


class TriageFeedbackResponse(BaseModel):
    """
    API response body for triage feedback submission.

    Attributes:
        status: Feedback recording status.
    """

    status: str


class TriageFeedbackSummaryResponse(BaseModel):
    """
    API response body for triage feedback summary.

    Attributes:
        total_feedback: Total number of feedback records.
        useful_count: Number of feedback records marked useful.
        not_useful_count: Number of feedback records marked not useful.
        useful_percentage: Percentage of feedback marked useful.
        recent_feedback: Recent feedback records, newest first.
    """

    total_feedback: int
    useful_count: int
    not_useful_count: int
    useful_percentage: float
    recent_feedback: list[dict[str, object]]


@dataclass
class TriageServiceProvider:
    """
    Lazily initializes and stores the triage service.

    Lazy initialization avoids loading the embedding model during import, which
    keeps tests and application startup more controllable.
    """

    service: TriageService | None = None

    def get_service(self) -> TriageService:
        """
        Return a ready-to-use triage service.

        Returns:
            TriageService with a built knowledge base retriever.
        """
        if self.service is None:
            retriever = KnowledgeBaseRetriever(docs_directory=DEFAULT_DOCS_DIRECTORY)
            retriever.build()
            self.service = TriageService(retriever=retriever)

        return self.service


service_provider = TriageServiceProvider()
request_logger = TriageRequestLogger(log_file_path=DEFAULT_LOG_FILE_PATH)
feedback_logger = TriageFeedbackLogger(log_file_path=DEFAULT_FEEDBACK_LOG_FILE_PATH)


@router.get("/history", response_model=TriageHistoryResponse)
def get_triage_history(limit: int = 10) -> TriageHistoryResponse:
    """
    Return recent triage request history.

    Args:
        limit: Maximum number of recent records to return.

    Returns:
        Recent triage request log records.

    Raises:
        HTTPException: If the limit is invalid or history cannot be read.
    """
    try:
        records = request_logger.read_recent(limit=limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return TriageHistoryResponse(records=records)


@router.post("/feedback", response_model=TriageFeedbackResponse)
def submit_triage_feedback(request: TriageFeedbackRequest) -> TriageFeedbackResponse:
    """
    Record user feedback for a triage result.

    Args:
        request: Feedback request containing triage result context and usefulness.

    Returns:
        Feedback recording status.

    Raises:
        HTTPException: If feedback cannot be written.
    """
    try:
        feedback_logger.log(
            ticket_text=request.ticket_text,
            category=request.category,
            severity=request.severity,
            useful=request.useful,
            notes=request.notes,
        )
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return TriageFeedbackResponse(status="recorded")


@router.get("/feedback/summary", response_model=TriageFeedbackSummaryResponse)
def get_triage_feedback_summary(recent_limit: int = 10) -> TriageFeedbackSummaryResponse:
    """
    Return summary statistics for triage feedback.

    Args:
        recent_limit: Maximum number of recent feedback records to include.

    Returns:
        Feedback summary with counts, percentage, and recent records.

    Raises:
        HTTPException: If the limit is invalid or feedback cannot be read.
    """
    try:
        summary = feedback_logger.summarize(recent_limit=recent_limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return TriageFeedbackSummaryResponse(**summary)


@router.post("", response_model=TriageResponse)
def triage_ticket(request: TriageRequest) -> TriageResponse:
    """
    Triage an IT support ticket or security alert.

    Args:
        request: Triage request containing ticket text and retrieval count.

    Returns:
        Structured triage result.

    Raises:
        HTTPException: If triage processing fails.
    """
    try:
        result = service_provider.get_service().triage_ticket(
            ticket_text=request.ticket_text,
            top_k=request.top_k,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    response = TriageResponse(
        ticket_text=result.ticket_text,
        category=result.classification.category.value,
        matched_keywords=result.classification.matched_keywords,
        severity=result.severity.severity.value,
        severity_score=result.severity.score,
        severity_reasons=result.severity.reasons,
        retrieved_evidence=[
            RetrievedEvidenceResponse(
                source_name=evidence.source_name,
                chunk_index=evidence.chunk_index,
                text=evidence.text,
                score=evidence.score,
                rank=evidence.rank,
            )
            for evidence in result.retrieved_evidence
        ],
    )

    try:
        request_logger.log(
            ticket_text=response.ticket_text,
            top_k=request.top_k,
            category=response.category,
            severity=response.severity,
            severity_score=response.severity_score,
            retrieved_sources=[evidence.source_name for evidence in result.retrieved_evidence],
        )
    except OSError:
        logger.warning("Failed to write triage request log.", exc_info=True)

    return response
