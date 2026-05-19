"""
Manual API demo script for the triage endpoint.

Run this script while the FastAPI server is running locally. It sends example
triage requests to POST /triage and prints the structured API response.
"""

from typing import Any

import httpx

API_URL = "http://127.0.0.1:8000/triage"
REQUEST_TIMEOUT_SECONDS = 60.0


def send_triage_request(ticket_text: str, top_k: int = 3) -> dict[str, Any]:
    """
    Send a triage request to the local FastAPI application.

    Args:
        ticket_text: Ticket, alert, or troubleshooting question to triage.
        top_k: Maximum number of evidence chunks to retrieve.

    Returns:
        Parsed JSON response from the API.

    Raises:
        httpx.HTTPStatusError: If the API returns an unsuccessful status code.
        httpx.RequestError: If the API server cannot be reached.
    """
    response = httpx.post(
        API_URL,
        json={
            "ticket_text": ticket_text,
            "top_k": top_k,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def print_triage_response(response_payload: dict[str, Any]) -> None:
    """
    Print a readable summary of the triage API response.

    Args:
        response_payload: Parsed JSON response returned by the API.
    """
    print("\n" + "=" * 80)
    print(f"Ticket: {response_payload['ticket_text']}")
    print("=" * 80)
    print(f"Category: {response_payload['category']}")
    print(f"Matched Keywords: {response_payload['matched_keywords']}")
    print(f"Severity: {response_payload['severity']}")
    print(f"Severity Score: {response_payload['severity_score']}")
    print("Severity Reasons:")

    for reason in response_payload["severity_reasons"]:
        print(f"  - {reason}")

    print("\nRetrieved Evidence:")

    for evidence in response_payload["retrieved_evidence"]:
        print(
            f"  Rank {evidence['rank']} | "
            f"{evidence['source_name']} | "
            f"Chunk {evidence['chunk_index']} | "
            f"Score {evidence['score']:.4f}"
        )


def main() -> None:
    """
    Send example requests to the local triage API.
    """
    example_tickets = [
        "Nginx logs show repeated 401 and 429 responses from the same external IP.",
        "User connects to VPN but cannot access internal resources.",
        "User cannot access shared drive after password reset.",
    ]

    for ticket_text in example_tickets:
        response_payload = send_triage_request(ticket_text=ticket_text, top_k=3)
        print_triage_response(response_payload=response_payload)


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print(
            "Could not connect to the API. Start the server first with:\n"
            "uvicorn app.main:app --reload"
        )
