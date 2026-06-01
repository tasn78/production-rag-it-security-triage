"""
Rule-based ticket classification for IT and security triage.

This module provides a deterministic baseline classifier. A simple rules-based
approach is useful early in the project because it is explainable, testable,
and predictable before adding LLM-based behavior.
"""

from app.triage.schemas import ClassificationResult, TriageCategory

CATEGORY_KEYWORDS: dict[TriageCategory, tuple[str, ...]] = {
    TriageCategory.SECURITY_ALERT: (
        "brute force",
        "password spraying",
        "credential stuffing",
        "suspicious",
        "threat",
        "attack",
        "unauthorized",
        "multiple failed",
        "repeated failed",
        "external ip",
        "blocked ip",
    ),
    TriageCategory.WEB_SERVER: (
        "nginx",
        "http 401",
        "http 403",
        "http 404",
        "http 429",
        "401",
        "403",
        "404",
        "429",
        "rate limit",
        "reverse proxy",
        "web server",
    ),
    TriageCategory.VPN_NETWORK_ACCESS: (
        "vpn",
        "internal resources",
        "internal systems",
        "dns",
        "remote access",
        "gateway",
        "split tunnel",
        "network access",
    ),
    TriageCategory.SHARED_DRIVE_ACCESS: (
        "shared drive",
        "mapped drive",
        "network drive",
        "file share",
        "unc path",
        "access denied",
        "folder permission",
        "group membership",
    ),
    TriageCategory.AUTHENTICATION: (
        "password reset",
        "resetting a forgotten password",
        "forgotten password",
        "forgot password",
        "reset password",
        "password help",
        "account locked",
        "account lockout",
        "mfa",
        "multi-factor",
        "authentication",
        "sign in",
        "login",
        "credentials",
        "cached credentials",
    ),
}


def normalize_ticket_text(ticket_text: str) -> str:
    """
    Normalize ticket text for keyword matching.

    Args:
        ticket_text: Raw ticket, alert, or issue description.

    Returns:
        Lowercase ticket text with repeated whitespace collapsed.

    Raises:
        ValueError: If ticket_text is empty or whitespace-only.
    """
    if not ticket_text or not ticket_text.strip():
        raise ValueError("ticket_text cannot be empty")

    return " ".join(ticket_text.lower().split())


def find_matching_keywords(ticket_text: str, keywords: tuple[str, ...]) -> list[str]:
    """
    Find keywords that appear in normalized ticket text.

    Args:
        ticket_text: Normalized ticket text.
        keywords: Candidate keywords for a category.

    Returns:
        List of matched keywords.
    """
    return [keyword for keyword in keywords if keyword in ticket_text]


def classify_ticket(ticket_text: str) -> ClassificationResult:
    """
    Classify a ticket into a high-level IT/security triage category.

    Categories are evaluated in priority order. Security-oriented categories are
    checked first so suspicious alerts are not misclassified as routine support.

    Args:
        ticket_text: Raw ticket, alert, or issue description.

    Returns:
        ClassificationResult containing the assigned category and matched keywords.

    Raises:
        ValueError: If ticket_text is empty or whitespace-only.
    """
    normalized_text = normalize_ticket_text(ticket_text)

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched_keywords = find_matching_keywords(
            ticket_text=normalized_text,
            keywords=keywords,
        )

        if matched_keywords:
            return ClassificationResult(
                category=category,
                matched_keywords=matched_keywords,
            )

    return ClassificationResult(
        category=TriageCategory.GENERAL_IT_SUPPORT,
        matched_keywords=[],
    )
