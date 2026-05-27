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
        request_id: str,
        ticket_text: str,
        category: str,
        severity: str,
        useful: bool,
        notes: str | None = None,
    ) -> None:
        """
        Append one triage feedback record to the JSONL log file.

        Args:
            request_id: Unique identifier for the triage request.
            ticket_text: Original ticket or alert text.
            category: Predicted triage category.
            severity: Predicted severity label.
            useful: Whether the user found the triage result useful.
            notes: Optional user feedback notes.
        """
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "ticket_text": ticket_text,
            "category": category,
            "severity": severity,
            "useful": useful,
            "notes": notes,
        }

        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_recent(self, limit: int = 10) -> list[dict[str, object]]:
        """
        Read the most recent triage feedback records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            Recent triage feedback records, newest first.
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

    def summarize(self, recent_limit: int = 10) -> dict[str, object]:
        """
        Summarize triage feedback records.

        Args:
            recent_limit: Maximum number of recent feedback records to include.

        Returns:
            Feedback summary with counts, percentage, and recent records.
        """
        if recent_limit < 1:
            raise ValueError("recent_limit must be greater than or equal to 1.")

        if not self.log_file_path.exists():
            return {
                "total_feedback": 0,
                "useful_count": 0,
                "not_useful_count": 0,
                "useful_percentage": 0.0,
                "recent_feedback": [],
            }

        records: list[dict[str, object]] = []

        with self.log_file_path.open("r", encoding="utf-8") as log_file:
            for line in log_file:
                line = line.strip()

                if not line:
                    continue

                records.append(json.loads(line))

        useful_count = sum(1 for record in records if record.get("useful") is True)
        total_feedback = len(records)
        not_useful_count = total_feedback - useful_count

        useful_percentage = (
            round((useful_count / total_feedback) * 100, 2) if total_feedback > 0 else 0.0
        )

        return {
            "total_feedback": total_feedback,
            "useful_count": useful_count,
            "not_useful_count": not_useful_count,
            "useful_percentage": useful_percentage,
            "recent_feedback": records[-recent_limit:][::-1],
        }
