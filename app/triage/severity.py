"""
Rule-based severity scoring for IT and security triage.

This module provides an explainable baseline severity scorer. It uses keywords,
affected-user indicators, and category context to assign Low, Medium, High, or
Critical severity levels.
"""

from app.triage.classifier import normalize_ticket_text
from app.triage.schemas import SeverityLevel, SeverityResult, TriageCategory


HIGH_RISK_SECURITY_KEYWORDS = (
    "brute force",
    "password spraying",
    "credential stuffing",
    "external ip",
    "unauthorized",
    "suspicious",
    "attack",
    "multiple failed",
    "repeated failed",
)

MULTI_USER_IMPACT_KEYWORDS = (
    "multiple users",
    "many users",
    "all users",
    "department",
    "company-wide",
    "outage",
    "unavailable",
)

PRIVILEGED_ACCESS_KEYWORDS = (
    "admin",
    "administrator",
    "privileged",
    "domain admin",
    "service account",
    "sensitive",
)


def map_score_to_severity(score: int) -> SeverityLevel:
    """
    Convert a numeric severity score into a severity level.

    Args:
        score: Numeric severity score.

    Returns:
        SeverityLevel corresponding to the score range.
    """
    if score >= 8:
        return SeverityLevel.CRITICAL

    if score >= 5:
        return SeverityLevel.HIGH

    if score >= 3:
        return SeverityLevel.MEDIUM

    return SeverityLevel.LOW


def calculate_severity(
    ticket_text: str,
    category: TriageCategory,
) -> SeverityResult:
    """
    Calculate severity for a ticket based on content and category.

    Args:
        ticket_text: Raw ticket, alert, or issue description.
        category: Category assigned by the classifier.

    Returns:
        SeverityResult containing severity level, numeric score, and reasons.

    Raises:
        ValueError: If ticket_text is empty or whitespace-only.
    """
    normalized_text = normalize_ticket_text(ticket_text)
    score = 1
    reasons = ["Base severity score applied."]

    if category == TriageCategory.SECURITY_ALERT:
        score += 3
        reasons.append("Security alert category increases severity.")

    if category == TriageCategory.WEB_SERVER:
        score += 1
        reasons.append("Web server issue may affect service availability.")

    matched_high_risk_keywords = [
        keyword for keyword in HIGH_RISK_SECURITY_KEYWORDS if keyword in normalized_text
    ]
    if matched_high_risk_keywords:
        score += 3
        reasons.append(
            "High-risk security indicators detected: "
            + ", ".join(matched_high_risk_keywords)
        )

    matched_multi_user_keywords = [
        keyword for keyword in MULTI_USER_IMPACT_KEYWORDS if keyword in normalized_text
    ]
    if matched_multi_user_keywords:
        score += 2
        reasons.append(
            "Multiple-user or service-impact indicators detected: "
            + ", ".join(matched_multi_user_keywords)
        )

    matched_privileged_keywords = [
        keyword for keyword in PRIVILEGED_ACCESS_KEYWORDS if keyword in normalized_text
    ]
    if matched_privileged_keywords:
        score += 2
        reasons.append(
            "Privileged or sensitive access indicators detected: "
            + ", ".join(matched_privileged_keywords)
        )

    severity = map_score_to_severity(score)

    return SeverityResult(
        severity=severity,
        score=score,
        reasons=reasons,
    )