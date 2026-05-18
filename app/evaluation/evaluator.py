"""
Evaluation utilities for the IT/security triage system.

This module evaluates the current triage pipeline against labeled examples and
computes classification, severity, and retrieval metrics.
"""

import json
from pathlib import Path

from app.evaluation.evaluation_schemas import EvaluationExample, EvaluationResult
from app.triage.service import TriageService


def load_evaluation_examples(file_path: Path) -> list[EvaluationExample]:
    """
    Load evaluation examples from a JSONL file.

    Args:
        file_path: Path to a JSONL evaluation dataset.

    Returns:
        List of EvaluationExample objects.

    Raises:
        FileNotFoundError: If the evaluation file does not exist.
        ValueError: If the file contains no usable examples.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Evaluation file does not exist: {file_path}")

    examples: list[EvaluationExample] = []

    for line_number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
            examples.append(
                EvaluationExample(
                    ticket_text=record["ticket_text"],
                    expected_category=record["expected_category"],
                    expected_severity=record["expected_severity"],
                    expected_source=record["expected_source"],
                )
            )
        except KeyError as error:
            raise ValueError(f"Missing required field on line {line_number}: {error}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}") from error

    if not examples:
        raise ValueError("evaluation file contains no examples")

    return examples


def evaluate_triage_service(
    triage_service: TriageService,
    examples: list[EvaluationExample],
    top_k: int = 3,
) -> list[EvaluationResult]:
    """
    Evaluate a triage service against labeled examples.

    Args:
        triage_service: TriageService instance to evaluate.
        examples: Labeled evaluation examples.
        top_k: Number of retrieved evidence chunks to evaluate.

    Returns:
        List of per-example EvaluationResult objects.

    Raises:
        ValueError: If examples is empty.
    """
    if not examples:
        raise ValueError("examples must contain at least one item")

    results: list[EvaluationResult] = []

    for example in examples:
        triage_result = triage_service.triage_ticket(
            ticket_text=example.ticket_text,
            top_k=top_k,
        )

        results.append(
            EvaluationResult(
                ticket_text=example.ticket_text,
                expected_category=example.expected_category,
                actual_category=triage_result.classification.category.value,
                expected_severity=example.expected_severity,
                actual_severity=triage_result.severity.severity.value,
                expected_source=example.expected_source,
                retrieved_sources=[
                    evidence.source_name for evidence in triage_result.retrieved_evidence
                ],
            )
        )

    return results


def calculate_accuracy(correct_count: int, total_count: int) -> float:
    """
    Calculate accuracy from correct and total counts.

    Args:
        correct_count: Number of correct predictions.
        total_count: Total number of predictions.

    Returns:
        Accuracy as a float between 0.0 and 1.0.

    Raises:
        ValueError: If total_count is less than or equal to zero.
    """
    if total_count <= 0:
        raise ValueError("total_count must be greater than 0")

    return correct_count / total_count


def summarize_evaluation_results(results: list[EvaluationResult]) -> dict[str, float]:
    """
    Summarize evaluation results into aggregate metrics.

    Args:
        results: Per-example evaluation results.

    Returns:
        Dictionary containing aggregate evaluation metrics.

    Raises:
        ValueError: If results is empty.
    """
    if not results:
        raise ValueError("results must contain at least one item")

    total_count = len(results)

    return {
        "category_accuracy": calculate_accuracy(
            sum(result.category_correct for result in results),
            total_count,
        ),
        "severity_accuracy": calculate_accuracy(
            sum(result.severity_correct for result in results),
            total_count,
        ),
        "retrieval_hit_at_k": calculate_accuracy(
            sum(result.retrieval_hit for result in results),
            total_count,
        ),
        "top_source_accuracy": calculate_accuracy(
            sum(result.top_source_correct for result in results),
            total_count,
        ),
    }