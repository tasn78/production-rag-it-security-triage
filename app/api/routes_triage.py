"""
FastAPI routes for IT and security triage.

This module exposes API endpoints for submitting tickets or alerts and receiving
structured triage output, including category, severity, and retrieved evidence.
"""

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.rag.retriever import KnowledgeBaseRetriever
from app.triage.service import TriageService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_DIRECTORY = PROJECT_ROOT / "data" / "docs"

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

    return TriageResponse(
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
