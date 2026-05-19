"""
Unit tests for embedding utility validation.

These tests focus on fast validation logic and avoid loading a real transformer
model so the test suite stays lightweight.
"""

import numpy as np
import pytest

from app.rag.embeddings import validate_embedding_matrix


def test_validate_embedding_matrix_accepts_valid_numeric_matrix() -> None:
    """
    Verify that a two-dimensional numeric matrix is accepted.
    """
    embeddings = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ],
        dtype=np.float32,
    )

    validate_embedding_matrix(embeddings)


def test_validate_embedding_matrix_rejects_one_dimensional_array() -> None:
    """
    Verify that embeddings must be a two-dimensional matrix.
    """
    embeddings = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    with pytest.raises(ValueError, match="two-dimensional matrix"):
        validate_embedding_matrix(embeddings)


def test_validate_embedding_matrix_rejects_empty_matrix() -> None:
    """
    Verify that embeddings must contain at least one row.
    """
    embeddings = np.empty((0, 3), dtype=np.float32)

    with pytest.raises(ValueError, match="at least one row"):
        validate_embedding_matrix(embeddings)


def test_validate_embedding_matrix_rejects_non_numeric_values() -> None:
    """
    Verify that embeddings must contain numeric values.
    """
    embeddings = np.array([["a", "b"], ["c", "d"]])

    with pytest.raises(ValueError, match="numeric values"):
        validate_embedding_matrix(embeddings)
