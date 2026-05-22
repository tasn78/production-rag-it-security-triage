"""
Local JSONL logging for triage feedback.

This module records lightweight user feedback for triage results so the system
can support future evaluation and improvement workflows.
"""

import json
from datetime import UTC, datetime
from pathlib import Path


class TriageFeedbackLogger:
    """
    Writes triage feedback records to a JSONL log file.
    """

    def __init__(self, log_file_path: Path) -> None:
        """
        Initialize the feedback logger.

        Args:
            log_file_path: Path to the JSONL feedback log file.
        """
        self.log_file_path = log_file_path

    def log(
        self,
        *,
        ticket_text: str,
        category: str,
        severity: str,
        useful: bool,
        notes: str | None = None,
    ) -> None:
        """
        Append one triage feedback record to the JSONL log file.

        Args:
            ticket_text: Original ticket or alert text.
            category: Predicted triage category.
            severity: Predicted severity label.
            useful: Whether the user found the triage result useful.
            notes: Optional user feedback notes.
        """
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "ticket_text": ticket_text,
            "category": category,
            "severity": severity,
            "useful": useful,
            "notes": notes,
        }

        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
