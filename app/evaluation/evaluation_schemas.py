"""
Shared schemas for evaluation workflows.

This module defines structured records used to evaluate classification,
severity scoring, and retrieval quality.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationExample:
    """
    Represents one labeled evaluation example.

    Attributes:
        ticket_text: Ticket or alert text to evaluate.
        expected_category: Expected triage category.
        expected_severity: Expected severity level.
        expected_source: Expected top supporting knowledge-base document.
    """

    ticket_text: str
    expected_category: str
    expected_severity: str
    expected_source: str


@dataclass(frozen=True)
class EvaluationResult:
    """
    Represents evaluation output for one example.

    Attributes:
        ticket_text: Evaluated ticket or alert text.
        expected_category: Expected category label.
        actual_category: Predicted category label.
        expected_severity: Expected severity label.
        actual_severity: Predicted severity label.
        expected_source: Expected evidence source document.
        retrieved_sources: Ranked retrieved source document names.
    """

    ticket_text: str
    expected_category: str
    actual_category: str
    expected_severity: str
    actual_severity: str
    expected_source: str
    retrieved_sources: list[str]

    @property
    def category_correct(self) -> bool:
        """
        Return whether the predicted category matches the expected category.
        """
        return self.actual_category == self.expected_category

    @property
    def severity_correct(self) -> bool:
        """
        Return whether the predicted severity matches the expected severity.
        """
        return self.actual_severity == self.expected_severity

    @property
    def retrieval_hit(self) -> bool:
        """
        Return whether the expected source appears in retrieved sources.
        """
        return self.expected_source in self.retrieved_sources

    @property
    def top_source_correct(self) -> bool:
        """
        Return whether the top retrieved source matches the expected source.
        """
        return bool(self.retrieved_sources) and self.retrieved_sources[0] == self.expected_source
