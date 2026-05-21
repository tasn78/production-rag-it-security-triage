"""
Streamlit dashboard for interactive IT and security triage.

This dashboard provides a simple user interface for submitting tickets or
security alerts and viewing classification, severity, and retrieved evidence.
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

DEFAULT_TICKET_TEXT = "Nginx logs show repeated 401 and 429 responses from the same external IP."


def run_triage_request(ticket_text: str, top_k: int) -> dict:
    """
    Send a triage request to the FastAPI backend.

    Args:
        ticket_text: Ticket or alert text submitted by the user.
        top_k: Number of evidence chunks to retrieve.

    Returns:
        Parsed JSON response from the FastAPI triage endpoint.
    """
    response = requests.post(
        f"{API_BASE_URL}/triage",
        json={
            "ticket_text": ticket_text,
            "top_k": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_triage_history(limit: int = 10) -> list[dict[str, object]]:
    """
    Fetch recent triage request history from the FastAPI backend.

    Args:
        limit: Maximum number of recent records to return.

    Returns:
        Recent triage request records.
    """
    response = requests.get(
        f"{API_BASE_URL}/triage/history",
        params={"limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("records", [])


def display_triage_result(ticket_text: str, top_k: int) -> None:
    """
    Run triage through the API and display structured results.

    Args:
        ticket_text: Ticket or alert text submitted by the user.
        top_k: Number of evidence chunks to retrieve.
    """
    try:
        result = run_triage_request(ticket_text=ticket_text, top_k=top_k)
    except requests.exceptions.RequestException as error:
        st.error(
            "The dashboard could not connect to the FastAPI backend. "
            f"Check that the API is running at {API_BASE_URL}."
        )
        st.exception(error)
        return

    st.subheader("Triage Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Category", result["category"])

    with col2:
        st.metric("Severity", result["severity"])

    with col3:
        st.metric("Severity Score", result["severity_score"])

    st.subheader("Matched Keywords")
    matched_keywords = result.get("matched_keywords", [])
    if matched_keywords:
        st.write(", ".join(matched_keywords))
    else:
        st.write("No specific keywords matched.")

    st.subheader("Severity Reasons")
    for reason in result.get("severity_reasons", []):
        st.write(f"- {reason}")

    st.subheader("Retrieved Evidence")

    for evidence in result.get("retrieved_evidence", []):
        with st.expander(
            f"Rank {evidence['rank']}: {evidence['source_name']} "
            f"(Chunk {evidence['chunk_index']}, Score {evidence['score']:.4f})"
        ):
            st.write(evidence["text"])


def display_triage_history() -> None:
    """
    Display recent triage request history in the dashboard.
    """
    st.subheader("Recent Triage History")

    try:
        records = get_triage_history(limit=10)
    except requests.exceptions.RequestException as error:
        st.warning(
            "Recent triage history is unavailable. "
            f"Check that the API is running at {API_BASE_URL}."
        )
        st.exception(error)
        return

    if not records:
        st.info("No triage history has been recorded yet.")
        return

    st.dataframe(
        records,
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    """
    Render the Streamlit triage dashboard.
    """
    st.set_page_config(
        page_title="IT and Security Triage",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("Production RAG System for IT and Security Triage")
    st.write(
        "Submit an IT support ticket or security alert to classify the issue, "
        "score severity, and retrieve supporting knowledge-base evidence."
    )

    ticket_text = st.text_area(
        "Ticket or alert text",
        value=DEFAULT_TICKET_TEXT,
        height=150,
    )

    top_k = st.slider(
        "Number of evidence chunks to retrieve",
        min_value=1,
        max_value=5,
        value=3,
    )

    if st.button("Run Triage"):
        if not ticket_text.strip():
            st.error("Please enter a ticket or alert description.")
            return

        with st.spinner("Running triage workflow..."):
            display_triage_result(ticket_text=ticket_text, top_k=top_k)

    st.divider()
    display_triage_history()


if __name__ == "__main__":
    main()
