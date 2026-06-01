"""
Deterministic triage summary generation.

This module creates concise, explainable summaries for triage results without
requiring an external LLM provider. The output can later be replaced or extended
with an optional LLM-backed provider while keeping the core triage workflow
testable and deterministic.
"""

from dataclasses import dataclass

from app.rag.retriever import RetrievalResult
from app.triage.schemas import SeverityResult, TriageCategory


@dataclass(frozen=True)
class TriageSummary:
    """
    Generated summary for a triage result.

    Attributes:
        summary_text: Concise plain-English explanation of the triage result.
        recommended_next_steps: Suggested next actions for review or escalation.
    """

    summary_text: str
    recommended_next_steps: list[str]


def generate_triage_summary(
    *,
    ticket_text: str,
    category: TriageCategory,
    severity: SeverityResult,
    retrieved_evidence: list[RetrievalResult],
) -> TriageSummary:
    """
    Generate a deterministic summary for a triage result.

    Args:
        ticket_text: Original ticket, alert, or issue description.
        category: Assigned triage category.
        severity: Assigned severity result.
        retrieved_evidence: Ranked knowledge-base evidence.

    Returns:
        TriageSummary containing summary text and recommended next steps.
    """
    top_source = (
        retrieved_evidence[0].source_name
        if retrieved_evidence
        else "no retrieved knowledge-base source"
    )

    summary_text = (
        f"This ticket was classified as {category.value} with "
        f"{severity.severity.value} severity based on the submitted issue text "
        f"and supporting evidence from {top_source}."
    )

    recommended_next_steps = _build_recommended_next_steps(
        category=category,
        severity=severity,
        top_source=top_source,
    )

    return TriageSummary(
        summary_text=summary_text,
        recommended_next_steps=recommended_next_steps,
    )


def _build_recommended_next_steps(
    *,
    category: TriageCategory,
    severity: SeverityResult,
    top_source: str,
) -> list[str]:
    """
    Build deterministic recommended next steps for a triage result.

    Args:
        category: Assigned triage category.
        severity: Assigned severity result.
        top_source: Highest-ranked retrieved source document.

    Returns:
        Recommended next steps.
    """
    next_steps = [
        f"Review the top retrieved knowledge-base source: {top_source}.",
        "Validate the ticket details against the matched keywords and severity reasons.",
    ]

    if category == TriageCategory.SECURITY_ALERT:
        next_steps.append(
            "Check logs for repeated failures, suspicious source IPs, and escalation indicators."
        )

    if category == TriageCategory.VPN_NETWORK_ACCESS:
        next_steps.append(
            "Verify VPN connectivity, DNS resolution, gateway status, "
            "and access to internal resources."
        )

    if category == TriageCategory.SHARED_DRIVE_ACCESS:
        next_steps.append(
            "Confirm group membership, mapped drive configuration, and shared folder permissions."
        )

    if category == TriageCategory.AUTHENTICATION:
        next_steps.append(
            "Verify account lockout status, password reset state, MFA status, "
            "and credential freshness."
        )

    if category == TriageCategory.WEB_SERVER:
        next_steps.append(
            "Review web server access logs, response codes, and rate-limiting behavior."
        )

    if severity.score >= 5:
        next_steps.append("Escalate if the issue affects multiple users or privileged access.")

    return next_steps
