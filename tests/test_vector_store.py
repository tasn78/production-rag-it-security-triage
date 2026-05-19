"""
Unit tests for the FAISS vector store.

These tests use deterministic numeric embeddings so they can validate search
behavior without loading a real embedding model.
"""

from pathlib import Path

import numpy as np
import pytest

from app.rag.knowledge_base import KnowledgeBaseChunk
from app.rag.vector_store import FaissVectorStore, VectorSearchResult


class FakeEmbedder:
    """
    Deterministic test embedder used to avoid loading a real transformer model.
    """

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Convert query text into predictable test embeddings.

        Args:
            texts: Text values to embed.

        Returns:
            A deterministic embedding matrix for testing.
        """
        embeddings = []

        for text in texts:
            if "vpn" in text.lower():
                embeddings.append([1.0, 0.0, 0.0])
            elif "nginx" in text.lower() or "401" in text.lower():
                embeddings.append([0.0, 1.0, 0.0])
            else:
                embeddings.append([0.0, 0.0, 1.0])

        return np.asarray(embeddings, dtype=np.float32)


def create_test_chunk(source_name: str, text: str, chunk_index: int) -> KnowledgeBaseChunk:
    """
    Create a KnowledgeBaseChunk for vector store tests.

    Args:
        source_name: Source document name.
        text: Chunk text.
        chunk_index: Chunk index within the source document.

    Returns:
        A KnowledgeBaseChunk with deterministic test metadata.
    """
    return KnowledgeBaseChunk(
        source_name=source_name,
        source_path=Path(f"/fake/{source_name}"),
        chunk_index=chunk_index,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_build_index_stores_chunks() -> None:
    """
    Verify that building an index stores the expected number of chunks.
    """
    chunks = [
        create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0),
        create_test_chunk("nginx_security.md", "Nginx security", 0),
    ]
    embeddings = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    assert vector_store.is_built is True
    assert vector_store.chunk_count == 2


def test_build_index_rejects_empty_chunks() -> None:
    """
    Verify that an index cannot be built without chunks.
    """
    vector_store = FaissVectorStore()
    embeddings = np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32)

    with pytest.raises(ValueError, match="chunks must contain at least one item"):
        vector_store.build_index(chunks=[], embeddings=embeddings)


def test_build_index_rejects_mismatched_chunk_and_embedding_counts() -> None:
    """
    Verify that each chunk must have a corresponding embedding row.
    """
    chunks = [create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0)]
    embeddings = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    vector_store = FaissVectorStore()

    with pytest.raises(ValueError, match="number of chunks must match"):
        vector_store.build_index(chunks=chunks, embeddings=embeddings)


def test_search_by_embedding_returns_ranked_results() -> None:
    """
    Verify that vector search returns the most similar chunk first.
    """
    chunks = [
        create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0),
        create_test_chunk("nginx_security.md", "Nginx security", 0),
    ]
    embeddings = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    results = vector_store.search_by_embedding(
        query_embedding=np.asarray([0.0, 1.0, 0.0], dtype=np.float32),
        top_k=2,
    )

    assert len(results) == 2
    assert all(isinstance(result, VectorSearchResult) for result in results)
    assert results[0].chunk.source_name == "nginx_security.md"
    assert results[0].rank == 1


def test_search_by_embedding_rejects_unbuilt_index() -> None:
    """
    Verify that searching before index construction raises RuntimeError.
    """
    vector_store = FaissVectorStore()

    with pytest.raises(RuntimeError, match="vector index has not been built"):
        vector_store.search_by_embedding(
            query_embedding=np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
            top_k=1,
        )


def test_search_by_embedding_rejects_invalid_top_k() -> None:
    """
    Verify that top_k must be greater than zero.
    """
    chunks = [create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0)]
    embeddings = np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32)

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    with pytest.raises(ValueError, match="top_k must be greater than 0"):
        vector_store.search_by_embedding(
            query_embedding=np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
            top_k=0,
        )


def test_search_by_embedding_rejects_dimension_mismatch() -> None:
    """
    Verify that query embedding dimensions must match the index dimension.
    """
    chunks = [create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0)]
    embeddings = np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32)

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    with pytest.raises(ValueError, match="dimension does not match"):
        vector_store.search_by_embedding(
            query_embedding=np.asarray([1.0, 0.0], dtype=np.float32),
            top_k=1,
        )


def test_search_uses_embedder_for_text_query() -> None:
    """
    Verify that raw text search uses the provided embedder and returns results.
    """
    chunks = [
        create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0),
        create_test_chunk("nginx_security.md", "Nginx security", 0),
    ]
    embeddings = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    results = vector_store.search(
        query_text="Nginx 401 errors",
        embedder=FakeEmbedder(),
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].chunk.source_name == "nginx_security.md"


def test_search_rejects_empty_query_text() -> None:
    """
    Verify that empty query text is rejected.
    """
    chunks = [create_test_chunk("vpn_troubleshooting.md", "VPN troubleshooting", 0)]
    embeddings = np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32)

    vector_store = FaissVectorStore()
    vector_store.build_index(chunks=chunks, embeddings=embeddings)

    with pytest.raises(ValueError, match="query_text cannot be empty"):
        vector_store.search(query_text="   ", embedder=FakeEmbedder(), top_k=1)
