"""
Unit tests for optional API key authentication.
"""

import pytest
from fastapi import HTTPException

from app.api.security import require_api_key


def test_require_api_key_allows_request_when_env_key_is_not_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that API key auth is disabled when TRIAGE_API_KEY is unset.
    """
    monkeypatch.delenv("TRIAGE_API_KEY", raising=False)

    require_api_key(x_api_key=None)


def test_require_api_key_allows_matching_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that a matching X-API-Key header is accepted.
    """
    monkeypatch.setenv("TRIAGE_API_KEY", "dev-secret-key")

    require_api_key(x_api_key="dev-secret-key")


def test_require_api_key_rejects_missing_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that a missing X-API-Key header is rejected when auth is enabled.
    """
    monkeypatch.setenv("TRIAGE_API_KEY", "dev-secret-key")

    with pytest.raises(HTTPException) as error:
        require_api_key(x_api_key=None)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid or missing API key."


def test_require_api_key_rejects_wrong_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that an incorrect X-API-Key header is rejected.
    """
    monkeypatch.setenv("TRIAGE_API_KEY", "dev-secret-key")

    with pytest.raises(HTTPException) as error:
        require_api_key(x_api_key="wrong-key")

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid or missing API key."


def test_require_api_key_treats_blank_env_value_as_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Verify that a blank TRIAGE_API_KEY value keeps local development mode open.
    """
    monkeypatch.setenv("TRIAGE_API_KEY", "   ")

    require_api_key(x_api_key=None)
