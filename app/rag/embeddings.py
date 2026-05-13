"""
Embedding utilities for converting text into dense vector representations.

This module provides a thin wrapper around SentenceTransformers so the rest of
the RAG pipeline can request embeddings without depending directly on the
underlying model implementation.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class TextEmbedder(Protocol):
    """
    Protocol for text embedding implementations.

    This allows production embedders and test embedders to share the same
    interface without requiring tests to load a real transformer model.
    """

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Convert a list of text strings into an embedding matrix.

        Args:
            texts: Text strings to embed.

        Returns:
            A NumPy array with shape (number_of_texts, embedding_dimension).
        """


@dataclass
class SentenceTransformerEmbedder:
    """
    SentenceTransformer-based implementation of the TextEmbedder protocol.

    Attributes:
        model_name: Name of the SentenceTransformer model to load.
    """

    model_name: str = DEFAULT_EMBEDDING_MODEL_NAME

    def __post_init__(self) -> None:
        """
        Load the SentenceTransformer model after dataclass initialization.
        """
        self._model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Convert text strings into normalized float32 embeddings.

        Args:
            texts: Text strings to embed.

        Returns:
            A float32 NumPy embedding matrix.

        Raises:
            ValueError: If no texts are provided.
        """
        if not texts:
            raise ValueError("texts must contain at least one item")

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return np.asarray(embeddings, dtype=np.float32)


def validate_embedding_matrix(embeddings: np.ndarray) -> None:
    """
    Validate that an embedding matrix is usable for vector search.

    Args:
        embeddings: NumPy array containing embeddings.

    Raises:
        ValueError: If embeddings are not a two-dimensional matrix.
        ValueError: If embeddings contain zero rows.
        ValueError: If embeddings are not numeric.
    """
    if embeddings.ndim != 2:
        raise ValueError("embeddings must be a two-dimensional matrix")

    if embeddings.shape[0] == 0:
        raise ValueError("embeddings must contain at least one row")

    if not np.issubdtype(embeddings.dtype, np.number):
        raise ValueError("embeddings must contain numeric values")