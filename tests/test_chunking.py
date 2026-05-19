"""
Unit tests for document chunking utilities.

These tests verify that raw source text can be normalized and split into
overlapping retrieval chunks with predictable metadata.
"""

import pytest

from app.rag.chunking import (
    TextChunk,
    create_overlapping_text_chunks,
    normalize_whitespace,
    validate_chunking_parameters,
)


def test_normalize_whitespace_collapses_repeated_spaces() -> None:
    """
    Verify that repeated spaces, newlines, and tabs collapse into single spaces.
    """
    text = "Password   reset\nrequires\tidentity verification."

    result = normalize_whitespace(text)

    assert result == "Password reset requires identity verification."


def test_validate_chunking_parameters_accepts_valid_values() -> None:
    """
    Verify that valid chunking parameters do not raise an exception.
    """
    validate_chunking_parameters(chunk_size=800, overlap=120)


def test_create_overlapping_text_chunks_returns_empty_list_for_empty_text() -> None:
    """
    Verify that empty or whitespace-only input returns no chunks.
    """
    assert create_overlapping_text_chunks("") == []
    assert create_overlapping_text_chunks("   ") == []


def test_create_overlapping_text_chunks_returns_single_chunk_for_short_text() -> None:
    """
    Verify that text shorter than the chunk size produces one TextChunk.
    """
    text = "Password resets require identity verification."

    chunks = create_overlapping_text_chunks(text, chunk_size=100, overlap=10)

    assert len(chunks) == 1
    assert isinstance(chunks[0], TextChunk)
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)


def test_create_overlapping_text_chunks_splits_long_text() -> None:
    """
    Verify that long text is split into multiple chunks.
    """
    text = "A" * 1000

    chunks = create_overlapping_text_chunks(text, chunk_size=400, overlap=100)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 400 for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_create_overlapping_text_chunks_preserves_overlap() -> None:
    """
    Verify that neighboring chunks preserve the configured overlap.
    """
    text = "A" * 1000

    chunks = create_overlapping_text_chunks(text, chunk_size=400, overlap=100)

    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 400
    assert chunks[1].start_char == 300


def test_create_overlapping_text_chunks_rejects_invalid_chunk_size() -> None:
    """
    Verify that chunk_size must be greater than zero.
    """
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        create_overlapping_text_chunks("test", chunk_size=0)


def test_create_overlapping_text_chunks_rejects_negative_overlap() -> None:
    """
    Verify that overlap cannot be negative.
    """
    with pytest.raises(ValueError, match="overlap cannot be negative"):
        create_overlapping_text_chunks("test", chunk_size=100, overlap=-1)


def test_create_overlapping_text_chunks_rejects_overlap_greater_than_chunk_size() -> None:
    """
    Verify that overlap must be smaller than chunk_size.
    """
    with pytest.raises(ValueError, match="overlap must be smaller than chunk_size"):
        create_overlapping_text_chunks("test", chunk_size=100, overlap=100)
