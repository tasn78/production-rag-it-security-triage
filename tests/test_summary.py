"""
Unit tests for deterministic triage summary generation.
"""

from app.rag.retriever import RetrievalResult
from app.triage.schemas import SeverityLevel, SeverityResult, TriageCategory
from app.triage.summary import generate_triage_summary


def test_generate_triage_summary_includes_category_severity_and_source() -> None:
    """
    Verify that generated summaries include key triage context.
    """
    severity = SeverityResult(
        severity=SeverityLevel.HIGH,
        score=7,
        reasons=["Security alert category increases severity."],
    )
    retrieved_evidence = [
        RetrievalResult(
            source_name="nginx_security.md",
            chunk_index=0,
            text="Nginx evidence text.",
            score=0.9,
            rank=1,
        )
    ]

    summary = generate_triage_summary(
        ticket_text="Nginx logs show repeated 401 responses.",
        category=TriageCategory.SECURITY_ALERT,
        severity=severity,
        retrieved_evidence=retrieved_evidence,
    )

    assert "Security Alert" in summary.summary_text
    assert "High" in summary.summary_text
    assert "nginx_security.md" in summary.summary_text
    assert summary.recommended_next_steps
    assert any("logs" in step.lower() for step in summary.recommended_next_steps)


def test_generate_triage_summary_handles_empty_evidence() -> None:
    """
    Verify that summary generation works without retrieved evidence.
    """
    severity = SeverityResult(
        severity=SeverityLevel.LOW,
        score=1,
        reasons=["Base severity score applied."],
    )

    summary = generate_triage_summary(
        ticket_text="General support request.",
        category=TriageCategory.GENERAL_IT_SUPPORT,
        severity=severity,
        retrieved_evidence=[],
    )

    assert "General IT Support" in summary.summary_text
    assert "no retrieved knowledge-base source" in summary.summary_text
    assert summary.recommended_next_steps
