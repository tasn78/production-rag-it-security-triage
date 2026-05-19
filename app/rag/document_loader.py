"""
Document loading utilities for the RAG knowledge base.

This module loads local Markdown and plain-text documents from the project
knowledge base directory. Loaded documents are later split into chunks,
embedded, indexed, and retrieved during IT/security triage.
"""

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_DOCUMENT_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class SourceDocument:
    """
    Represents a source document loaded from the local knowledge base.

    Attributes:
        source_path: Full filesystem path to the document.
        source_name: File name used for citations and display.
        text: Raw document text loaded from disk.
    """

    source_path: Path
    source_name: str
    text: str


def is_supported_document_file(file_path: Path) -> bool:
    """
    Determine whether a file path points to a supported document type.

    Args:
        file_path: Path to evaluate.

    Returns:
        True if the path is a file with a supported extension; otherwise False.
    """
    return file_path.is_file() and file_path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS


def load_text_file(file_path: Path) -> str:
    """
    Load text content from a UTF-8 encoded document file.

    Args:
        file_path: Path to the document file.

    Returns:
        Raw text content from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path does not point to a supported document type.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Document file does not exist: {file_path}")

    if not is_supported_document_file(file_path):
        raise ValueError(f"Unsupported document file type: {file_path.suffix}")

    return file_path.read_text(encoding="utf-8")


def load_documents_from_directory(directory_path: Path) -> list[SourceDocument]:
    """
    Load all supported documents from a directory.

    Args:
        directory_path: Directory containing Markdown or plain-text source documents.

    Returns:
        A list of SourceDocument objects sorted by file name.

    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path exists but is not a directory.
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Document directory does not exist: {directory_path}")

    if not directory_path.is_dir():
        raise NotADirectoryError(f"Document path is not a directory: {directory_path}")

    documents: list[SourceDocument] = []

    for file_path in sorted(directory_path.iterdir()):
        if is_supported_document_file(file_path):
            documents.append(
                SourceDocument(
                    source_path=file_path,
                    source_name=file_path.name,
                    text=load_text_file(file_path),
                )
            )

    return documents
