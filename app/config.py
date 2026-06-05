"""
Application configuration helpers.

Configuration is loaded from environment variables so local development,
Docker Compose, and future cloud deployments can change behavior without
modifying application code.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

USE_ML_CLASSIFIER = os.getenv("USE_ML_CLASSIFIER", "false").strip().lower() == "true"

ML_CATEGORY_MODEL_PATH = Path(
    os.getenv(
        "ML_CATEGORY_MODEL_PATH",
        str(PROJECT_ROOT / "models" / "category_classifier.joblib"),
    )
)
