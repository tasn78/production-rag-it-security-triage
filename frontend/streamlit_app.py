"""
Streamlit dashboard for interactive IT and security triage.

This dashboard provides a simple user interface for submitting tickets or
security alerts and viewing classification, severity, and retrieved evidence.
"""

# ruff: noqa: E402, I001

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.retriever import KnowledgeBaseRetriever
from app.triage.service import TriageService


DOCS_DIRECTORY = PROJECT_ROOT / "data" / "docs"

DEFAULT_TICKET_TEXT = "Nginx logs show repeated 401 and 429 responses from the same external IP."


@st.cache_resource
def load_triage_service() -> TriageService:
    """
    Build and cache the triage service for Streamlit sessions.

    Returns:
        TriageService with a built knowledge base retriever.
    """
    retriever = KnowledgeBaseRetriever(docs_directory=DOCS_DIRECTORY)
    retriever.build()
    return TriageService(retriever=retriever)


def display_triage_result(ticket_text: str, top_k: int) -> None:
    """
    Run triage and display structured results in the dashboard.

    Args:
        ticket_text: Ticket or alert text submitted by the user.
        top_k: Number of evidence chunks to retrieve.
    """
    triage_service = load_triage_service()
    result = triage_service.triage_ticket(ticket_text=ticket_text, top_k=top_k)

    st.subheader("Triage Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Category", result.classification.category.value)

    with col2:
        st.metric("Severity", result.severity.severity.value)

    with col3:
        st.metric("Severity Score", result.severity.score)

    st.subheader("Matched Keywords")
    if result.classification.matched_keywords:
        st.write(", ".join(result.classification.matched_keywords))
    else:
        st.write("No specific keywords matched.")

    st.subheader("Severity Reasons")
    for reason in result.severity.reasons:
        st.write(f"- {reason}")

    st.subheader("Retrieved Evidence")

    for evidence in result.retrieved_evidence:
        with st.expander(
            f"Rank {evidence.rank}: {evidence.source_name} "
            f"(Chunk {evidence.chunk_index}, Score {evidence.score:.4f})"
        ):
            st.write(evidence.text)


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


if __name__ == "__main__":
    main()
