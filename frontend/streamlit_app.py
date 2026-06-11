"""
Streamlit dashboard for interactive IT and security triage.

This dashboard provides a simple user interface for submitting tickets or
security alerts and viewing classification, severity, and retrieved evidence.
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TRIAGE_API_KEY = os.getenv("TRIAGE_API_KEY", "").strip()

DEFAULT_TICKET_TEXT = "Nginx logs show repeated 401 and 429 responses from the same external IP."


def build_api_headers() -> dict[str, str]:
    """
    Build optional API headers for FastAPI requests.

    Returns:
        Request headers containing X-API-Key when configured.
    """
    if not TRIAGE_API_KEY:
        return {}

    return {"X-API-Key": TRIAGE_API_KEY}


def format_classifier_mode(classifier_mode: str) -> str:
    """
    Format classifier mode values for dashboard display.

    Args:
        classifier_mode: Raw classifier mode value returned by the API.

    Returns:
        Human-readable classifier mode label.
    """
    classifier_mode_labels = {
        "rule_based": "Rule-based",
        "ml": "ML classifier",
        "ml_fallback_rule_based": "ML fallback to rule-based",
    }

    return classifier_mode_labels.get(classifier_mode, classifier_mode or "Unknown")


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
        headers=build_api_headers(),
        json={
            "ticket_text": ticket_text,
            "top_k": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_api_health() -> dict[str, str]:
    """
    Fetch FastAPI backend health metadata.

    Returns:
        API health metadata.
    """
    response = requests.get(
        f"{API_BASE_URL}/health",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def build_triage_report(result: dict, ticket_text: str) -> str:
    """
    Build a Markdown report for a triage result.

    Args:
        result: Parsed JSON response from the FastAPI triage endpoint.
        ticket_text: Original ticket or alert text.

    Returns:
        Markdown triage report.
    """
    matched_keywords = result.get("matched_keywords", [])
    severity_reasons = result.get("severity_reasons", [])
    retrieved_evidence = result.get("retrieved_evidence", [])
    summary = result.get("summary", {})
    classifier_mode = format_classifier_mode(result.get("classifier_mode", ""))
    recommended_next_steps = summary.get("recommended_next_steps", [])

    report_lines = [
        "# IT and Security Triage Report",
        "",
        f"Request ID: {result['request_id']}",
        "",
        "## Ticket or Alert Text",
        "",
        ticket_text,
        "",
        "## Triage Summary",
        "",
        f"- Category: {result['category']}",
        f"- Classifier Mode: {classifier_mode}",
        f"- Severity: {result['severity']}",
        f"- Severity Score: {result['severity_score']}",
        "",
        "## Generated Triage Summary",
        "",
        summary.get("summary_text", "No summary returned."),
        "",
        "## Recommended Next Steps",
        "",
    ]

    if recommended_next_steps:
        report_lines.extend(f"- {step}" for step in recommended_next_steps)
    else:
        report_lines.append("No recommended next steps returned.")

    report_lines.extend(
        [
            "",
            "## Matched Keywords",
            "",
            ", ".join(matched_keywords) if matched_keywords else "No specific keywords matched.",
            "",
            "## Severity Reasons",
            "",
        ]
    )

    if severity_reasons:
        report_lines.extend(f"- {reason}" for reason in severity_reasons)
    else:
        report_lines.append("No severity reasons returned.")

    report_lines.extend(
        [
            "",
            "## Retrieved Evidence",
            "",
        ]
    )

    if retrieved_evidence:
        for evidence in retrieved_evidence:
            report_lines.extend(
                [
                    f"### Rank {evidence['rank']}: {evidence['source_name']}",
                    "",
                    f"- Chunk Index: {evidence['chunk_index']}",
                    f"- Score: {evidence['score']:.4f}",
                    "",
                    "```text",
                    evidence["text"],
                    "```",
                    "",
                ]
            )
    else:
        report_lines.append("No retrieved evidence returned.")

    return "\n".join(report_lines)


def display_triage_response(result: dict, ticket_text: str) -> None:
    """
    Display a triage API response and feedback form.

    Args:
        result: Parsed JSON response from the FastAPI triage endpoint.
        ticket_text: Original ticket or alert text.
    """
    st.subheader("Triage Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Category", result["category"])

    with col2:
        st.metric(
            "Classifier Mode",
            format_classifier_mode(result.get("classifier_mode", "")),
        )

    with col3:
        st.metric("Severity", result["severity"])

    with col4:
        st.metric("Severity Score", result["severity_score"])

    summary = result.get("summary", {})
    if summary:
        st.subheader("Generated Triage Summary")
        st.write(summary.get("summary_text", "No summary returned"))

        recommended_next_steps = summary.get("recommended_next_steps", [])
        if recommended_next_steps:
            st.write("Recommended Next Steps")
            for step in recommended_next_steps:
                st.write(f"- {step}")

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

    report = build_triage_report(result=result, ticket_text=ticket_text)
    st.download_button(
        label="Download Triage Report",
        data=report,
        file_name=f"triage_report_{result['request_id']}.md",
        mime="text/markdown",
    )

    display_feedback_form(
        request_id=result["request_id"],
        ticket_text=ticket_text,
        category=result["category"],
        severity=result["severity"],
    )


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
        headers=build_api_headers(),
        params={"limit": limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("records", [])


def get_feedback_summary(recent_limit: int = 10) -> dict[str, object]:
    """
    Fetch feedback summary metrics from the FastAPI backend.

    Args:
        recent_limit: Maximum number of recent feedback records to include.

    Returns:
        Feedback summary metrics and recent feedback records.
    """
    response = requests.get(
        f"{API_BASE_URL}/triage/feedback/summary",
        headers=build_api_headers(),
        params={"recent_limit": recent_limit},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def submit_triage_feedback(
    *,
    request_id: str,
    ticket_text: str,
    category: str,
    severity: str,
    useful: bool,
    notes: str | None,
) -> None:
    """
    Submit user feedback for a triage result to the FastAPI backend.

    Args:
        request_id: Unique identifier for the triage request.
        ticket_text: Original ticket or alert text.
        category: Triage category returned by the API.
        severity: Severity returned by the API.
        useful: Whether the triage result was useful.
        notes: Optional feedback notes.
    """
    response = requests.post(
        f"{API_BASE_URL}/triage/feedback",
        headers=build_api_headers(),
        json={
            "request_id": request_id,
            "ticket_text": ticket_text,
            "category": category,
            "severity": severity,
            "useful": useful,
            "notes": notes,
        },
        timeout=30,
    )
    response.raise_for_status()


def display_triage_result(ticket_text: str, top_k: int) -> None:
    """
    Run triage through the API and store the result in session state.

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

    st.session_state["latest_triage_result"] = result
    st.session_state["latest_ticket_text"] = ticket_text


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


def display_api_status() -> None:
    """
    Display FastAPI backend connection status in the dashboard.
    """
    st.subheader("System Status")

    try:
        health = get_api_health()
    except requests.exceptions.RequestException as error:
        st.error(f"API backend is unavailable. Check that the API is running at {API_BASE_URL}.")
        st.exception(error)
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("API Status", health.get("status", "unknown"))

    with col2:
        st.metric("Service Version", health.get("version", "unknown"))

    with col3:
        st.metric("Backend URL", API_BASE_URL)

    st.caption(health.get("service", "Production RAG System for IT and Security Triage"))


def display_feedback_summary() -> None:
    """
    Display feedback summary metrics in the dashboard.
    """
    st.subheader("Feedback Summary")

    try:
        summary = get_feedback_summary(recent_limit=10)
    except requests.exceptions.RequestException as error:
        st.warning(
            f"Feedback summary is unavailable. Check that the API is running at {API_BASE_URL}."
        )
        st.exception(error)
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Feedback", summary["total_feedback"])

    with col2:
        st.metric("Useful", summary["useful_count"])

    with col3:
        st.metric("Not Useful", summary["not_useful_count"])

    with col4:
        st.metric("Useful %", f"{summary['useful_percentage']}%")

    recent_feedback = summary.get("recent_feedback", [])

    if recent_feedback:
        st.write("Recent Feedback")
        st.dataframe(
            recent_feedback,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No feedback has been recorded yet.")


def display_feedback_form(
    request_id: str,
    ticket_text: str,
    category: str,
    severity: str,
) -> None:
    """
    Display a feedback form for the most recent triage result.

    Args:
        request_id: Unique identifier for the triage request.
        ticket_text: Original ticket or alert text.
        category: Triage category returned by the API.
        severity: Severity returned by the API.
    """
    st.subheader("Triage Feedback")

    useful_label = st.radio(
        "Was this triage result useful?",
        options=["Yes", "No"],
        horizontal=True,
    )
    notes = st.text_area(
        "Optional feedback notes",
        placeholder="Example: The category was correct, but the severity was too high.",
    )

    if st.button("Submit Feedback"):
        try:
            submit_triage_feedback(
                request_id=request_id,
                ticket_text=ticket_text,
                category=category,
                severity=severity,
                useful=useful_label == "Yes",
                notes=notes.strip() or None,
            )
        except requests.exceptions.RequestException as error:
            st.error(
                f"Feedback could not be submitted. Check that the API is running at {API_BASE_URL}."
            )
            st.exception(error)
            return

        st.success("Feedback recorded.")


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

    if "latest_triage_result" in st.session_state:
        display_triage_response(
            result=st.session_state["latest_triage_result"],
            ticket_text=st.session_state["latest_ticket_text"],
        )

    st.divider()
    display_api_status()

    st.divider()
    display_feedback_summary()

    st.divider()
    display_triage_history()


if __name__ == "__main__":
    main()
