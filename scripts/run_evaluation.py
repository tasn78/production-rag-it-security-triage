"""
Run evaluation for the local IT/security triage system.

This script builds the retriever, creates the triage service, evaluates labeled
examples, and prints aggregate metrics.
"""

from pathlib import Path

from app.evaluation.evaluator import (
    evaluate_triage_service,
    load_evaluation_examples,
    summarize_evaluation_results,
)
from app.rag.retriever import KnowledgeBaseRetriever
from app.triage.service import TriageService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIRECTORY = PROJECT_ROOT / "data" / "docs"
EVAL_SET_PATH = PROJECT_ROOT / "data" / "eval_set.jsonl"


def main() -> None:
    """
    Run the evaluation workflow and print metrics.
    """
    examples = load_evaluation_examples(EVAL_SET_PATH)

    retriever = KnowledgeBaseRetriever(docs_directory=DOCS_DIRECTORY)
    retriever.build()

    triage_service = TriageService(retriever=retriever)

    results = evaluate_triage_service(
        triage_service=triage_service,
        examples=examples,
        top_k=3,
    )

    metrics = summarize_evaluation_results(results)

    print("\nEvaluation Metrics")
    print("=" * 80)

    for metric_name, metric_value in metrics.items():
        print(f"{metric_name}: {metric_value:.2%}")

    print("\nPer-example Results")
    print("=" * 80)

    for result in results:
        print(f"\nTicket: {result.ticket_text}")
        print(f"Expected Category: {result.expected_category}")
        print(f"Actual Category:   {result.actual_category}")
        print(f"Expected Severity: {result.expected_severity}")
        print(f"Actual Severity:   {result.actual_severity}")
        print(f"Expected Source:   {result.expected_source}")
        print(f"Retrieved Sources: {result.retrieved_sources}")
        print(f"Category Correct:  {result.category_correct}")
        print(f"Severity Correct:  {result.severity_correct}")
        print(f"Retrieval Hit:     {result.retrieval_hit}")
        print(f"Top Source Correct:{result.top_source_correct}")


if __name__ == "__main__":
    main()
