"""
Unit tests for rule-based ticket classification.

These tests verify that common IT and security ticket examples are assigned to
the expected triage categories.
"""

import pytest

from app.triage.classifier import classify_ticket, normalize_ticket_text
from app.triage.schemas import TriageCategory


def test_normalize_ticket_text_collapses_whitespace_and_lowercases() -> None:
    """
    Verify that ticket text is normalized before keyword matching.
    """
    result = normalize_ticket_text(" User   Cannot\nAccess\tVPN ")

    assert result == "user cannot access vpn"


def test_normalize_ticket_text_rejects_empty_text() -> None:
    """
    Verify that empty ticket text raises ValueError.
    """
    with pytest.raises(ValueError, match="ticket_text cannot be empty"):
        normalize_ticket_text("   ")


def test_classify_ticket_detects_security_alert() -> None:
    """
    Verify that suspicious authentication behavior is classified as security.
    """
    result = classify_ticket(
        "Repeated failed login attempts from an external IP may indicate brute force activity."
    )

    assert result.category == TriageCategory.SECURITY_ALERT
    assert "brute force" in result.matched_keywords


def test_classify_ticket_detects_web_server_issue() -> None:
    """
    Verify that Nginx and HTTP status code alerts classify as web server issues.
    """
    result = classify_ticket("Nginx logs show repeated 401 and 429 responses.")

    assert result.category == TriageCategory.WEB_SERVER
    assert "nginx" in result.matched_keywords


def test_classify_ticket_detects_vpn_network_access_issue() -> None:
    """
    Verify that VPN connectivity issues classify as network access issues.
    """
    result = classify_ticket("User connects to VPN but cannot access internal resources.")

    assert result.category == TriageCategory.VPN_NETWORK_ACCESS
    assert "vpn" in result.matched_keywords


def test_classify_ticket_detects_shared_drive_access_issue() -> None:
    """
    Verify that shared drive issues classify as file access issues.
    """
    result = classify_ticket("User cannot access shared drive after password reset.")

    assert result.category == TriageCategory.SHARED_DRIVE_ACCESS
    assert "shared drive" in result.matched_keywords


def test_classify_ticket_detects_authentication_issue() -> None:
    """
    Verify that password and account issues classify as authentication issues.
    """
    result = classify_ticket("User account locked after password reset.")

    assert result.category == TriageCategory.AUTHENTICATION
    assert "password reset" in result.matched_keywords


def test_classify_ticket_defaults_to_general_it_support() -> None:
    """
    Verify that unmatched tickets fall back to general IT support.
    """
    result = classify_ticket("User reports that their monitor flickers occasionally.")

    assert result.category == TriageCategory.GENERAL_IT_SUPPORT
    assert result.matched_keywords == []
