"""
Unit tests for local document loading utilities.

These tests verify that the RAG pipeline can load supported knowledge base
documents while rejecting unsupported files and invalid paths.
"""

from pathlib import Path

import pytest

from app.rag.document_loader import (
    SourceDocument,
    is_supported_document_file,
    load_documents_from_directory,
    load_text_file,
)


def test_is_supported_document_file_accepts_markdown_and_text(tmp_path: Path) -> None:
    """
    Verify that Markdown and plain-text files are supported document types.
    """
    markdown_file = tmp_path / "vpn_troubleshooting.md"
    text_file = tmp_path / "password_reset.txt"

    markdown_file.write_text("# VPN Troubleshooting", encoding="utf-8")
    text_file.write_text("Password reset guide", encoding="utf-8")

    assert is_supported_document_file(markdown_file) is True
    assert is_supported_document_file(text_file) is True


def test_is_supported_document_file_rejects_unsupported_file_types(tmp_path: Path) -> None:
    """
    Verify that unsupported file extensions are rejected.
    """
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text("ticket_id,text", encoding="utf-8")

    assert is_supported_document_file(csv_file) is False


def test_load_text_file_reads_supported_file(tmp_path: Path) -> None:
    """
    Verify that a supported text file can be loaded from disk.
    """
    document_file = tmp_path / "shared_drive_access.md"
    document_file.write_text("Shared drive access requires group membership.", encoding="utf-8")

    result = load_text_file(document_file)

    assert result == "Shared drive access requires group membership."


def test_load_text_file_rejects_missing_file(tmp_path: Path) -> None:
    """
    Verify that loading a missing file raises FileNotFoundError.
    """
    missing_file = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError, match="Document file does not exist"):
        load_text_file(missing_file)


def test_load_text_file_rejects_unsupported_file_type(tmp_path: Path) -> None:
    """
    Verify that unsupported file types raise ValueError.
    """
    unsupported_file = tmp_path / "data.csv"
    unsupported_file.write_text("not,a,document", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported document file type"):
        load_text_file(unsupported_file)


def test_load_documents_from_directory_loads_supported_documents(tmp_path: Path) -> None:
    """
    Verify that supported documents are loaded and sorted by file name.
    """
    first_file = tmp_path / "nginx_security.md"
    second_file = tmp_path / "vpn_troubleshooting.txt"
    ignored_file = tmp_path / "tickets.csv"

    first_file.write_text("Nginx security guide", encoding="utf-8")
    second_file.write_text("VPN troubleshooting guide", encoding="utf-8")
    ignored_file.write_text("ticket_id,text", encoding="utf-8")

    documents = load_documents_from_directory(tmp_path)

    assert len(documents) == 2
    assert all(isinstance(document, SourceDocument) for document in documents)
    assert [document.source_name for document in documents] == [
        "nginx_security.md",
        "vpn_troubleshooting.txt",
    ]


def test_load_documents_from_directory_rejects_missing_directory(tmp_path: Path) -> None:
    """
    Verify that a missing directory raises FileNotFoundError.
    """
    missing_directory = tmp_path / "missing_docs"

    with pytest.raises(FileNotFoundError, match="Document directory does not exist"):
        load_documents_from_directory(missing_directory)


def test_load_documents_from_directory_rejects_file_path(tmp_path: Path) -> None:
    """
    Verify that passing a file instead of a directory raises NotADirectoryError.
    """
    file_path = tmp_path / "not_a_directory.md"
    file_path.write_text("This is a file, not a directory.", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="Document path is not a directory"):
        load_documents_from_directory(file_path)