"""
Local JSONL logging for triage requests.

This module records lightweight triage request summaries for debugging,
auditing, and future dashboard history features.
"""

import json
from datetime import UTC, datetime
from pathlib import Path


class TriageRequestLogger:
    """
    Writes triage request summaries to a JSONL log file.
    """

    def __init__(self, log_file_path: Path) -> None:
        """
        Initialize the request logger.

        Args:
            log_file_path: Path to the JSONL log file.
        """
        self.log_file_path = log_file_path

    def log(
        self,
        *,
        ticket_text: str,
        top_k: int,
        category: str,
        severity: str,
        severity_score: int,
        retrieved_sources: list[str],
    ) -> None:
        """
        Append one triage request summary to the JSONL log file.

        Args:
            ticket_text: Original ticket or alert text.
            top_k: Requested number of evidence chunks.
            category: Predicted triage category.
            severity: Predicted severity label.
            severity_score: Numeric severity score.
            retrieved_sources: Source document names returned by retrieval.
        """
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "ticket_text": ticket_text,
            "top_k": top_k,
            "category": category,
            "severity": severity,
            "severity_score": severity_score,
            "retrieved_sources": retrieved_sources,
        }

        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
