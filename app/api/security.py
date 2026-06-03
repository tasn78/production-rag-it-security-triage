"""
Optional API key authentication for protected API endpoints.

Authentication is disabled by default for local development. If the
TRIAGE_API_KEY environment variable is set, protected endpoints require the
same value in the X-API-Key request header.
"""

import os
import secrets

from fastapi import Header, HTTPException, status

API_KEY_ENV_VAR = "TRIAGE_API_KEY"


def get_configured_api_key() -> str | None:
    """
    Read the configured API key from the environment.

    Returns:
        Configured API key, or None when API key protection is disabled.
    """
    api_key = os.getenv(API_KEY_ENV_VAR)

    if api_key is None or not api_key.strip():
        return None

    return api_key


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Require a valid API key when API key protection is enabled.

    Args:
        x_api_key: API key supplied through the X-API-Key request header.

    Raises:
        HTTPException: If API key protection is enabled and the supplied key is
            missing or invalid.
    """
    configured_api_key = get_configured_api_key()

    if configured_api_key is None:
        return

    if x_api_key is None or not secrets.compare_digest(x_api_key, configured_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
