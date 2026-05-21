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

    def read_recent(self, limit: int = 10) -> list[dict[str, object]]:
        """
        Read the most recent triage request log records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            Recent triage request records, newest first.
        """
        if limit < 1:
            raise ValueError("limit must be greater than or equal to 1.")

        if not self.log_file_path.exists():
            return []

        records: list[dict[str, object]] = []

        with self.log_file_path.open("r", encoding="utf-8") as log_file:
            for line in log_file:
                line = line.strip()

                if not line:
                    continue

                records.append(json.loads(line))

        return records[-limit:][::-1]
