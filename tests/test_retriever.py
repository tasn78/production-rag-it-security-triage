"""
Unit tests for the high-level knowledge base retriever.

These tests verify that local documents can be loaded, chunked, embedded with a
deterministic test embedder, indexed, and searched for relevant results.
"""

from pathlib import Path

import numpy as np
import pytest

from app.rag.retriever import KnowledgeBaseRetriever, RetrievalResult


class FakeKeywordEmbedder:
    """
    Deterministic keyword-based embedder for retriever tests.

    The fake embedder avoids loading a real transformer model while preserving
    predictable similarity behavior for VPN, Nginx, and password topics.
    """

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Convert text into deterministic three-dimensional embeddings.

        Args:
            texts: Text values to embed.

        Returns:
            Numeric embedding matrix.
        """
        embeddings = []

        for text in texts:
            normalized_text = text.lower()

            if "nginx" in normalized_text or "401" in normalized_text or "429" in normalized_text:
                embeddings.append([1.0, 0.0, 0.0])
            elif "vpn" in normalized_text or "internal resources" in normalized_text:
                embeddings.append([0.0, 1.0, 0.0])
            elif "password" in normalized_text or "account lockout" in normalized_text:
                embeddings.append([0.0, 0.0, 1.0])
            else:
                embeddings.append([0.3, 0.3, 0.3])

        return np.asarray(embeddings, dtype=np.float32)


def test_retriever_builds_index_from_local_documents(tmp_path: Path) -> None:
    """
    Verify that the retriever builds a search index from local documents.
    """
    docs_directory = tmp_path / "docs"
    docs_directory.mkdir()

    (docs_directory / "nginx_security.md").write_text(
        "Nginx logs with repeated 401 and 429 responses may indicate brute-force activity.",
        encoding="utf-8",
    )
    (docs_directory / "vpn_troubleshooting.md").write_text(
        "VPN users may fail to access internal resources because of DNS issues.",
        encoding="utf-8",
    )

    retriever = KnowledgeBaseRetriever(
        docs_directory=docs_directory,
        embedder=FakeKeywordEmbedder(),
        chunk_size=300,
        overlap=50,
    )

    retriever.build()

    assert retriever.is_ready is True
    assert retriever.chunk_count == 2


def test_retriever_returns_relevant_nginx_result(tmp_path: Path) -> None:
    """
    Verify that an Nginx-related query retrieves the Nginx source document first.
    """
    docs_directory = tmp_path / "docs"
    docs_directory.mkdir()

    (docs_directory / "nginx_security.md").write_text(
        "Nginx security guide explains repeated 401 and 429 status codes.",
        encoding="utf-8",
    )
    (docs_directory / "vpn_troubleshooting.md").write_text(
        "VPN troubleshooting explains internal resources and DNS failures.",
        encoding="utf-8",
    )

    retriever = KnowledgeBaseRetriever(
        docs_directory=docs_directory,
        embedder=FakeKeywordEmbedder(),
        chunk_size=300,
        overlap=50,
    )
    retriever.build()

    results = retriever.retrieve(
        query_text="Nginx logs show repeated 401 and 429 responses.",
        top_k=1,
    )

    assert len(results) == 1
    assert isinstance(results[0], RetrievalResult)
    assert results[0].source_name == "nginx_security.md"
    assert results[0].rank == 1
    assert "401" in results[0].text


def test_retriever_returns_relevant_vpn_result(tmp_path: Path) -> None:
    """
    Verify that a VPN-related query retrieves the VPN source document first.
    """
    docs_directory = tmp_path / "docs"
    docs_directory.mkdir()

    (docs_directory / "nginx_security.md").write_text(
        "Nginx security guide explains repeated 401 and 429 status codes.",
        encoding="utf-8",
    )
    (docs_directory / "vpn_troubleshooting.md").write_text(
        "VPN troubleshooting explains internal resources and DNS failures.",
        encoding="utf-8",
    )

    retriever = KnowledgeBaseRetriever(
        docs_directory=docs_directory,
        embedder=FakeKeywordEmbedder(),
        chunk_size=300,
        overlap=50,
    )
    retriever.build()

    results = retriever.retrieve(
        query_text="User connects to VPN but cannot access internal resources.",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].source_name == "vpn_troubleshooting.md"


def test_retriever_rejects_search_before_build(tmp_path: Path) -> None:
    """
    Verify that retrieval cannot run before the index is built.
    """
    retriever = KnowledgeBaseRetriever(
        docs_directory=tmp_path,
        embedder=FakeKeywordEmbedder(),
    )

    with pytest.raises(RuntimeError, match="retriever index has not been built"):
        retriever.retrieve(query_text="Nginx 401 errors", top_k=1)


def test_retriever_rejects_empty_knowledge_base(tmp_path: Path) -> None:
    """
    Verify that building a retriever with no supported documents raises an error.
    """
    docs_directory = tmp_path / "docs"
    docs_directory.mkdir()

    retriever = KnowledgeBaseRetriever(
        docs_directory=docs_directory,
        embedder=FakeKeywordEmbedder(),
    )

    with pytest.raises(ValueError, match="knowledge base contains no chunks"):
        retriever.build()
