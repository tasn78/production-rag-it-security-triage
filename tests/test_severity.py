"""
Unit tests for rule-based severity scoring.

These tests verify that category context and ticket keywords produce predictable
severity scores and explanation reasons.
"""

import pytest

from app.triage.schemas import SeverityLevel, TriageCategory
from app.triage.severity import calculate_severity, map_score_to_severity


def test_map_score_to_severity_returns_low_for_small_score() -> None:
    """
    Verify that low numeric scores map to Low severity.
    """
    assert map_score_to_severity(1) == SeverityLevel.LOW


def test_map_score_to_severity_returns_medium_for_moderate_score() -> None:
    """
    Verify that moderate numeric scores map to Medium severity.
    """
    assert map_score_to_severity(3) == SeverityLevel.MEDIUM


def test_map_score_to_severity_returns_high_for_high_score() -> None:
    """
    Verify that high numeric scores map to High severity.
    """
    assert map_score_to_severity(5) == SeverityLevel.HIGH


def test_map_score_to_severity_returns_critical_for_critical_score() -> None:
    """
    Verify that very high numeric scores map to Critical severity.
    """
    assert map_score_to_severity(8) == SeverityLevel.CRITICAL


def test_calculate_severity_scores_security_alert_as_high() -> None:
    """
    Verify that suspicious external authentication activity receives high severity.
    """
    result = calculate_severity(
        ticket_text=(
            "Repeated failed login attempts from an external IP indicate brute force activity."
        ),
        category=TriageCategory.SECURITY_ALERT,
    )

    assert result.severity in {SeverityLevel.HIGH, SeverityLevel.CRITICAL}
    assert result.score >= 5
    assert any("Security alert category" in reason for reason in result.reasons)


def test_calculate_severity_scores_multi_user_outage_higher() -> None:
    """
    Verify that multiple-user impact increases severity.
    """
    result = calculate_severity(
        ticket_text="Multiple users report that the VPN gateway is unavailable.",
        category=TriageCategory.VPN_NETWORK_ACCESS,
    )

    assert result.severity in {SeverityLevel.MEDIUM, SeverityLevel.HIGH}
    assert result.score >= 3
    assert any("Multiple-user" in reason for reason in result.reasons)


def test_calculate_severity_scores_privileged_access_higher() -> None:
    """
    Verify that privileged account issues increase severity.
    """
    result = calculate_severity(
        ticket_text="Admin account has repeated failed login attempts.",
        category=TriageCategory.AUTHENTICATION,
    )

    assert result.severity in {SeverityLevel.MEDIUM, SeverityLevel.HIGH}
    assert result.score >= 3
    assert any("Privileged" in reason for reason in result.reasons)


def test_calculate_severity_scores_routine_issue_as_low() -> None:
    """
    Verify that routine single-user support issues remain Low severity.
    """
    result = calculate_severity(
        ticket_text="User reports that their monitor flickers occasionally.",
        category=TriageCategory.GENERAL_IT_SUPPORT,
    )

    assert result.severity == SeverityLevel.LOW
    assert result.score == 1


def test_calculate_severity_rejects_empty_ticket_text() -> None:
    """
    Verify that empty ticket text is rejected.
    """
    with pytest.raises(ValueError, match="ticket_text cannot be empty"):
        calculate_severity("   ", TriageCategory.GENERAL_IT_SUPPORT)
