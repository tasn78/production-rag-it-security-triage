"""
Manual demo script for local knowledge base retrieval.

Run this script to verify that the RAG retrieval layer can load the sample
IT/security documents, build a vector index, and retrieve relevant chunks for
example triage queries.
"""

from pathlib import Path

from app.rag.retriever import KnowledgeBaseRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIRECTORY = PROJECT_ROOT / "data" / "docs"


def print_results(
    retriever: KnowledgeBaseRetriever,
    query_text: str,
    top_k: int = 3,
) -> None:
    """
    Print ranked retrieval results for a query.

    Args:
        retriever: Built knowledge base retriever.
        query_text: User ticket, alert, or troubleshooting question.
        top_k: Maximum number of retrieval results to display.
    """
    results = retriever.retrieve(query_text=query_text, top_k=top_k)

    print("\n" + "=" * 80)
    print(f"Query: {query_text}")
    print("=" * 80)

    for result in results:
        print(f"\nRank: {result.rank}")
        print(f"Source: {result.source_name}")
        print(f"Chunk: {result.chunk_index}")
        print(f"Score: {result.score:.4f}")
        print(f"Text: {result.text[:500]}...")


def main() -> None:
    """
    Build the retriever once and run example retrieval queries.
    """
    retriever = KnowledgeBaseRetriever(docs_directory=DOCS_DIRECTORY)
    retriever.build()

    example_queries = [
        "Nginx logs show repeated 401 and 429 responses from the same external IP.",
        "User connects to VPN but cannot access internal resources.",
        "User cannot access shared drive after password reset.",
    ]

    for query in example_queries:
        print_results(retriever=retriever, query_text=query)


if __name__ == "__main__":
    main()