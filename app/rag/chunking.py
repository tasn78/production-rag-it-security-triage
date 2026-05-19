"""
Utilities for splitting source documents into retrieval-friendly text chunks.

This module contains the first stage of the RAG pipeline. It normalizes raw
document text and converts it into overlapping chunks that can later be embedded,
indexed, retrieved, and cited in triage responses.
"""

from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


@dataclass(frozen=True)
class TextChunk:
    """
    Represents a retrieval-ready chunk created from a larger document.

    Attributes:
        text: The chunk content used for embedding and retrieval.
        chunk_index: The zero-based position of the chunk within the source text.
        start_char: The starting character offset in the normalized source text.
        end_char: The ending character offset in the normalized source text.
    """

    text: str
    chunk_index: int
    start_char: int
    end_char: int


def normalize_whitespace(text: str) -> str:
    """
    Collapse repeated whitespace into single spaces.

    Normalizing whitespace creates more consistent chunks across markdown,
    plain text, copied logs, and support documents.

    Args:
        text: Raw source document text.

    Returns:
        Text with repeated whitespace collapsed into single spaces.
    """
    return " ".join(text.split())


def validate_chunking_parameters(chunk_size: int, overlap: int) -> None:
    """
    Validate chunking configuration before splitting text.

    Args:
        chunk_size: Maximum number of characters allowed per chunk.
        overlap: Number of characters shared between neighboring chunks.

    Raises:
        ValueError: If chunk_size is less than or equal to zero.
        ValueError: If overlap is negative.
        ValueError: If overlap is greater than or equal to chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")


def create_overlapping_text_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """
    Split normalized document text into overlapping chunks for retrieval.

    Overlap preserves context across chunk boundaries, which can improve
    retrieval quality when relevant information appears near the edge of a chunk.

    Args:
        text: Raw source document text.
        chunk_size: Maximum number of characters allowed per chunk.
        overlap: Number of characters shared between neighboring chunks.

    Returns:
        A list of TextChunk objects containing chunk text and position metadata.

    Raises:
        ValueError: If chunk_size is less than or equal to zero.
        ValueError: If overlap is negative.
        ValueError: If overlap is greater than or equal to chunk_size.
    """
    validate_chunking_parameters(chunk_size=chunk_size, overlap=overlap)

    if not text or not text.strip():
        return []

    normalized_text = normalize_whitespace(text)
    chunks: list[TextChunk] = []

    start_char = 0
    chunk_index = 0
    text_length = len(normalized_text)

    while start_char < text_length:
        end_char = min(start_char + chunk_size, text_length)
        chunk_content = normalized_text[start_char:end_char].strip()

        if chunk_content:
            chunks.append(
                TextChunk(
                    text=chunk_content,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            chunk_index += 1

        if end_char >= text_length:
            break

        # Step backward by the overlap amount so context is preserved between chunks.
        start_char = end_char - overlap

    return chunks
