"""
ML-based ticket category classification.

This module wraps a trained scikit-learn text-classification pipeline. The ML
classifier is optional and is used only when enabled through configuration.
"""

from pathlib import Path
from typing import Any

import joblib

from app.triage.schemas import ClassificationResult, TriageCategory


class MLCategoryClassifier:
    """
    Optional ML classifier for ticket category prediction.

    The classifier expects a saved scikit-learn pipeline that accepts raw ticket
    text and predicts one of the project's triage category labels.
    """

    def __init__(self, model_path: Path) -> None:
        """
        Initialize the ML classifier.

        Args:
            model_path: Path to a trained joblib model pipeline.
        """
        self._model_path = model_path
        self._pipeline: Any | None = None

    @property
    def is_available(self) -> bool:
        """
        Return whether the ML model has been loaded successfully.

        Returns:
            True when the model pipeline is loaded, otherwise False.
        """
        return self._pipeline is not None

    def load(self) -> None:
        """
        Load the trained model pipeline from disk.

        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        if not self._model_path.exists():
            raise FileNotFoundError(f"ML category model not found: {self._model_path}")

        self._pipeline = joblib.load(self._model_path)

    def predict(self, ticket_text: str) -> ClassificationResult:
        """
        Predict a triage category for a ticket.

        Args:
            ticket_text: Raw ticket or alert text.

        Returns:
            ClassificationResult containing the predicted category.

        Raises:
            RuntimeError: If the ML model has not been loaded.
            ValueError: If the model predicts an unknown category.
        """
        if self._pipeline is None:
            raise RuntimeError("ML category model has not been loaded.")

        predicted_label = str(self._pipeline.predict([ticket_text])[0])

        try:
            category = TriageCategory(predicted_label)
        except ValueError as error:
            raise ValueError(f"Unknown ML category prediction: {predicted_label}") from error

        return ClassificationResult(
            category=category,
            matched_keywords=[],
        )
