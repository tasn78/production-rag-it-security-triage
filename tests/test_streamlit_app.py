"""
Unit tests for Streamlit dashboard helper functions.

These tests cover pure helper logic without launching the Streamlit app.
"""

from frontend.streamlit_app import build_triage_report


def test_build_triage_report_includes_core_triage_fields() -> None:
    """
    Verify that the Markdown triage report includes key triage fields.
    """
    result = {
        "request_id": "test-request-id",
        "category": "Security Alert",
        "severity": "High",
        "severity_score": 7,
        "matched_keywords": ["external ip"],
        "severity_reasons": [
            "Base severity score applied.",
            "Security alert category increases severity.",
        ],
        "summary": {
            "summary_text": ("This ticket was classified as Security Alert with High severity."),
            "recommended_next_steps": [
                "Review the top retrieved knowledge-base source: nginx_security.md.",
                "Check logs for repeated failures.",
            ],
        },
        "retrieved_evidence": [
            {
                "rank": 1,
                "source_name": "nginx_security.md",
                "chunk_index": 0,
                "score": 0.7079,
                "text": "Nginx evidence text.",
            }
        ],
    }
    ticket_text = "Nginx logs show repeated 401 and 429 responses."

    report = build_triage_report(result=result, ticket_text=ticket_text)

    assert "# IT and Security Triage Report" in report
    assert "Request ID: test-request-id" in report
    assert ticket_text in report
    assert "- Category: Security Alert" in report
    assert "- Severity: High" in report
    assert "- Severity Score: 7" in report
    assert "## Generated Triage Summary" in report
    assert "This ticket was classified as Security Alert with High severity." in report
    assert "## Recommended Next Steps" in report
    assert "- Review the top retrieved knowledge-base source: nginx_security.md." in report
    assert "- Check logs for repeated failures." in report
    assert "external ip" in report
    assert "- Base severity score applied." in report
    assert "### Rank 1: nginx_security.md" in report
    assert "- Chunk Index: 0" in report
    assert "- Score: 0.7079" in report
    assert "```text" in report
    assert "Nginx evidence text." in report
