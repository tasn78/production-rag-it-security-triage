"""
Knowledge base utilities for preparing source documents for retrieval.

This module connects document loading and chunking. It converts local source
documents into retrieval-ready chunks with source metadata preserved for
citations and debugging.
"""

from dataclasses import dataclass
from pathlib import Path

from app.rag.chunking import TextChunk, create_overlapping_text_chunks
from app.rag.document_loader import SourceDocument, load_documents_from_directory


@dataclass(frozen=True)
class KnowledgeBaseChunk:
    """
    Represents a retrieval-ready chunk with source document metadata.

    Attributes:
        source_name: Name of the source document used for citation.
        source_path: Full path to the source document.
        chunk_index: Zero-based chunk index within the source document.
        text: Chunk text used for embedding and retrieval.
        start_char: Starting character offset in the normalized source document.
        end_char: Ending character offset in the normalized source document.
    """

    source_name: str
    source_path: Path
    chunk_index: int
    text: str
    start_char: int
    end_char: int


def create_knowledge_base_chunks(
    documents: list[SourceDocument],
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[KnowledgeBaseChunk]:
    """
    Convert source documents into retrieval-ready knowledge base chunks.

    Args:
        documents: Source documents loaded from the knowledge base directory.
        chunk_size: Maximum number of characters allowed per chunk.
        overlap: Number of characters shared between neighboring chunks.

    Returns:
        A list of KnowledgeBaseChunk objects with source metadata preserved.
    """
    knowledge_base_chunks: list[KnowledgeBaseChunk] = []

    for document in documents:
        text_chunks: list[TextChunk] = create_overlapping_text_chunks(
            text=document.text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for text_chunk in text_chunks:
            knowledge_base_chunks.append(
                KnowledgeBaseChunk(
                    source_name=document.source_name,
                    source_path=document.source_path,
                    chunk_index=text_chunk.chunk_index,
                    text=text_chunk.text,
                    start_char=text_chunk.start_char,
                    end_char=text_chunk.end_char,
                )
            )

    return knowledge_base_chunks


def load_knowledge_base_chunks(
    docs_directory: Path,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[KnowledgeBaseChunk]:
    """
    Load local documents and convert them into retrieval-ready chunks.

    Args:
        docs_directory: Directory containing supported source documents.
        chunk_size: Maximum number of characters allowed per chunk.
        overlap: Number of characters shared between neighboring chunks.

    Returns:
        A list of KnowledgeBaseChunk objects ready for embedding and retrieval.

    Raises:
        FileNotFoundError: If the document directory does not exist.
        NotADirectoryError: If the document path is not a directory.
        ValueError: If chunking parameters are invalid.
    """
    documents = load_documents_from_directory(docs_directory)
    return create_knowledge_base_chunks(
        documents=documents,
        chunk_size=chunk_size,
        overlap=overlap,
    )
