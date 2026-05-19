"""
High-level retrieval service for the RAG knowledge base.

This module connects knowledge base loading, text embeddings, and FAISS vector
search into a single reusable retriever. The retriever is responsible for
building the local search index and returning citation-ready chunks for a user
ticket, alert, or troubleshooting question.
"""

from dataclasses import dataclass
from pathlib import Path

from app.rag.embeddings import SentenceTransformerEmbedder, TextEmbedder
from app.rag.knowledge_base import KnowledgeBaseChunk, load_knowledge_base_chunks
from app.rag.vector_store import FaissVectorStore, VectorSearchResult

DEFAULT_RETRIEVAL_TOP_K = 3


@dataclass(frozen=True)
class RetrievalResult:
    """
    Represents a citation-ready retrieval result.

    Attributes:
        source_name: Name of the source document used for citation.
        chunk_index: Zero-based chunk index within the source document.
        text: Retrieved chunk text.
        score: Similarity score returned by vector search.
        rank: One-based rank in the retrieval results.
    """

    source_name: str
    chunk_index: int
    text: str
    score: float
    rank: int


class KnowledgeBaseRetriever:
    """
    End-to-end retriever for local IT/security knowledge base documents.

    The retriever loads source documents, chunks them, embeds the chunks, builds
    a FAISS vector index, and searches that index for relevant context.
    """

    def __init__(
        self,
        docs_directory: Path,
        embedder: TextEmbedder | None = None,
        chunk_size: int = 800,
        overlap: int = 120,
    ) -> None:
        """
        Initialize the retriever configuration.

        Args:
            docs_directory: Directory containing Markdown or plain-text documents.
            embedder: Text embedding implementation. If omitted, a
                SentenceTransformer-based embedder is used.
            chunk_size: Maximum number of characters allowed per chunk.
            overlap: Number of characters shared between neighboring chunks.
        """
        self._docs_directory = docs_directory
        self._embedder = embedder or SentenceTransformerEmbedder()
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._vector_store = FaissVectorStore()
        self._chunks: list[KnowledgeBaseChunk] = []

    @property
    def is_ready(self) -> bool:
        """
        Return whether the retriever has built its search index.

        Returns:
            True if the vector store is built; otherwise False.
        """
        return self._vector_store.is_built

    @property
    def chunk_count(self) -> int:
        """
        Return the number of chunks available for retrieval.

        Returns:
            Number of indexed knowledge base chunks.
        """
        return self._vector_store.chunk_count

    def build(self) -> None:
        """
        Load documents, create chunks, embed them, and build the vector index.

        Raises:
            FileNotFoundError: If the document directory does not exist.
            NotADirectoryError: If the document path is not a directory.
            ValueError: If no chunks are produced or embeddings are invalid.
        """
        chunks = load_knowledge_base_chunks(
            docs_directory=self._docs_directory,
            chunk_size=self._chunk_size,
            overlap=self._overlap,
        )

        if not chunks:
            raise ValueError("knowledge base contains no chunks to index")

        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self._embedder.embed_texts(chunk_texts)

        self._vector_store.build_index(chunks=chunks, embeddings=embeddings)
        self._chunks = chunks

    def retrieve(
        self,
        query_text: str,
        top_k: int = DEFAULT_RETRIEVAL_TOP_K,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant knowledge base chunks for a query.

        Args:
            query_text: User ticket, security alert, or troubleshooting question.
            top_k: Maximum number of retrieval results to return.

        Returns:
            Ranked retrieval results with source metadata.

        Raises:
            RuntimeError: If the retriever has not been built.
            ValueError: If query_text is empty or top_k is invalid.
        """
        if not self.is_ready:
            raise RuntimeError("retriever index has not been built")

        search_results = self._vector_store.search(
            query_text=query_text,
            embedder=self._embedder,
            top_k=top_k,
        )

        return [self._to_retrieval_result(search_result) for search_result in search_results]

    @staticmethod
    def _to_retrieval_result(search_result: VectorSearchResult) -> RetrievalResult:
        """
        Convert a vector search result into a public retrieval result.

        Args:
            search_result: Internal vector search result.

        Returns:
            Citation-ready retrieval result.
        """
        return RetrievalResult(
            source_name=search_result.chunk.source_name,
            chunk_index=search_result.chunk.chunk_index,
            text=search_result.chunk.text,
            score=search_result.score,
            rank=search_result.rank,
        )
