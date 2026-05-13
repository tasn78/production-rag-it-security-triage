"""
Vector store utilities for indexing and searching knowledge base chunks.

This module uses FAISS for similarity search over dense embedding vectors.
The vector store keeps chunk metadata alongside the FAISS index so retrieved
results can be displayed with source citations.
"""

from dataclasses import dataclass

import faiss
import numpy as np

from app.rag.embeddings import TextEmbedder, validate_embedding_matrix
from app.rag.knowledge_base import KnowledgeBaseChunk


@dataclass(frozen=True)
class VectorSearchResult:
    """
    Represents a single vector search result.

    Attributes:
        chunk: Retrieved knowledge base chunk.
        score: Similarity score returned by the vector index.
        rank: One-based rank in the search results.
    """

    chunk: KnowledgeBaseChunk
    score: float
    rank: int


class FaissVectorStore:
    """
    FAISS-backed vector store for knowledge base chunk retrieval.

    This implementation uses inner product search. When embeddings are
    normalized, inner product is equivalent to cosine similarity.
    """

    def __init__(self) -> None:
        """
        Initialize an empty FAISS vector store.
        """
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: list[KnowledgeBaseChunk] = []
        self._embedding_dimension: int | None = None

    @property
    def is_built(self) -> bool:
        """
        Return whether the vector index has been built.

        Returns:
            True if the index exists and contains chunks; otherwise False.
        """
        return self._index is not None and len(self._chunks) > 0

    @property
    def chunk_count(self) -> int:
        """
        Return the number of chunks stored in the vector index.

        Returns:
            Number of indexed knowledge base chunks.
        """
        return len(self._chunks)

    def build_index(
        self,
        chunks: list[KnowledgeBaseChunk],
        embeddings: np.ndarray,
    ) -> None:
        """
        Build a FAISS index from knowledge base chunks and embeddings.

        Args:
            chunks: Knowledge base chunks associated with the embeddings.
            embeddings: Embedding matrix with one row per chunk.

        Raises:
            ValueError: If no chunks are provided.
            ValueError: If the number of chunks does not match embedding rows.
            ValueError: If the embedding matrix is invalid.
        """
        if not chunks:
            raise ValueError("chunks must contain at least one item")

        validate_embedding_matrix(embeddings)

        if len(chunks) != embeddings.shape[0]:
            raise ValueError("number of chunks must match number of embedding rows")

        normalized_embeddings = np.asarray(embeddings, dtype=np.float32)
        embedding_dimension = normalized_embeddings.shape[1]

        index = faiss.IndexFlatIP(embedding_dimension)
        index.add(normalized_embeddings)

        self._index = index
        self._chunks = list(chunks)
        self._embedding_dimension = embedding_dimension

    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
    ) -> list[VectorSearchResult]:
        """
        Search for the most relevant chunks using a query embedding.

        Args:
            query_embedding: One-dimensional query embedding vector.
            top_k: Maximum number of results to return.

        Returns:
            Ranked vector search results.

        Raises:
            RuntimeError: If the index has not been built.
            ValueError: If top_k is less than or equal to zero.
            ValueError: If the query embedding shape is invalid.
        """
        if not self.is_built or self._index is None:
            raise RuntimeError("vector index has not been built")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        query_vector = np.asarray(query_embedding, dtype=np.float32)

        if query_vector.ndim != 1:
            raise ValueError("query_embedding must be a one-dimensional vector")

        if self._embedding_dimension is None:
            raise RuntimeError("embedding dimension is unavailable")

        if query_vector.shape[0] != self._embedding_dimension:
            raise ValueError("query_embedding dimension does not match index dimension")

        query_matrix = query_vector.reshape(1, -1)
        search_limit = min(top_k, len(self._chunks))

        scores, indices = self._index.search(query_matrix, search_limit)

        results: list[VectorSearchResult] = []

        for rank, chunk_index in enumerate(indices[0], start=1):
            if chunk_index == -1:
                continue

            results.append(
                VectorSearchResult(
                    chunk=self._chunks[int(chunk_index)],
                    score=float(scores[0][rank - 1]),
                    rank=rank,
                )
            )

        return results

    def search(
        self,
        query_text: str,
        embedder: TextEmbedder,
        top_k: int = 3,
    ) -> list[VectorSearchResult]:
        """
        Search for relevant chunks using a raw text query.

        Args:
            query_text: User ticket, alert, or troubleshooting question.
            embedder: Text embedding implementation.
            top_k: Maximum number of results to return.

        Returns:
            Ranked vector search results.

        Raises:
            ValueError: If query_text is empty or whitespace-only.
        """
        if not query_text or not query_text.strip():
            raise ValueError("query_text cannot be empty")

        query_embeddings = embedder.embed_texts([query_text])
        validate_embedding_matrix(query_embeddings)

        return self.search_by_embedding(
            query_embedding=query_embeddings[0],
            top_k=top_k,
        )