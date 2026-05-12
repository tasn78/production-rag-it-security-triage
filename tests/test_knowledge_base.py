"""
Unit tests for knowledge base preparation utilities.

These tests verify that source documents can be converted into retrieval-ready
chunks while preserving citation metadata.
"""

from pathlib import Path

from app.rag.document_loader import SourceDocument
from app.rag.knowledge_base import (
    KnowledgeBaseChunk,
    create_knowledge_base_chunks,
    load_knowledge_base_chunks,
)


def test_create_knowledge_base_chunks_preserves_source_metadata(tmp_path: Path) -> None:
    """
    Verify that chunks retain source document name, path, and chunk metadata.
    """
    source_path = tmp_path / "password_reset.md"
    document = SourceDocument(
        source_path=source_path,
        source_name="password_reset.md",
        text="Password reset troubleshooting requires identity verification.",
    )

    chunks = create_knowledge_base_chunks(
        documents=[document],
        chunk_size=100,
        overlap=10,
    )

    assert len(chunks) == 1
    assert isinstance(chunks[0], KnowledgeBaseChunk)
    assert chunks[0].source_name == "password_reset.md"
    assert chunks[0].source_path == source_path
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == document.text


def test_create_knowledge_base_chunks_handles_multiple_documents(tmp_path: Path) -> None:
    """
    Verify that chunks can be created from multiple source documents.
    """
    first_document = SourceDocument(
        source_path=tmp_path / "nginx_security.md",
        source_name="nginx_security.md",
        text="Repeated 401 and 429 responses may indicate brute-force activity.",
    )
    second_document = SourceDocument(
        source_path=tmp_path / "vpn_troubleshooting.md",
        source_name="vpn_troubleshooting.md",
        text="VPN users may fail to access internal resources because of DNS issues.",
    )

    chunks = create_knowledge_base_chunks(
        documents=[first_document, second_document],
        chunk_size=100,
        overlap=10,
    )

    assert len(chunks) == 2
    assert [chunk.source_name for chunk in chunks] == [
        "nginx_security.md",
        "vpn_troubleshooting.md",
    ]


def test_load_knowledge_base_chunks_loads_documents_from_directory(tmp_path: Path) -> None:
    """
    Verify that supported files can be loaded and converted into chunks.
    """
    first_file = tmp_path / "shared_drive_access.md"
    second_file = tmp_path / "password_reset.txt"

    first_file.write_text("Shared drive access requires group membership.", encoding="utf-8")
    second_file.write_text("Password resets require identity verification.", encoding="utf-8")

    chunks = load_knowledge_base_chunks(
        docs_directory=tmp_path,
        chunk_size=100,
        overlap=10,
    )

    assert len(chunks) == 2
    assert all(isinstance(chunk, KnowledgeBaseChunk) for chunk in chunks)
    assert [chunk.source_name for chunk in chunks] == [
        "password_reset.txt",
        "shared_drive_access.md",
    ]