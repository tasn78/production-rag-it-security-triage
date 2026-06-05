"""
Train a ticket category classifier.

This script trains a baseline ML classifier for ticket category prediction using
the generated local training dataset. It supports multiple model choices so the
project can compare simple, deployable text-classification baselines.

Generated model artifacts are written under models/ and are not committed to Git.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "training" / "category_training_set.csv"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "models" / "category_classifier.joblib"

RANDOM_STATE = 42
TEST_SIZE = 0.2

SUPPORTED_MODELS = ("lr", "svm")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Train a ticket category classifier.",
    )
    parser.add_argument(
        "--model",
        choices=SUPPORTED_MODELS,
        default="lr",
        help="Model type to train. Options: lr, svm.",
    )
    parser.add_argument(
        "--training-data",
        type=Path,
        default=TRAINING_DATA_PATH,
        help="Path to category_training_set.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MODEL_OUTPUT_PATH,
        help="Path where the trained model pipeline should be saved.",
    )

    return parser.parse_args()


def load_training_data(path: Path) -> pd.DataFrame:
    """
    Load the category training dataset.

    Args:
        path: Path to the generated category training CSV.

    Returns:
        Training dataframe.

    Raises:
        FileNotFoundError: If the training dataset does not exist.
        ValueError: If required columns are missing or no usable rows exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {path}. "
            "Run python -m scripts.build_training_dataset first."
        )

    dataframe = pd.read_csv(path)

    required_columns = {"ticket_text", "category"}
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(f"Training data is missing columns: {sorted(missing_columns)}")

    dataframe = dataframe.copy()
    dataframe["ticket_text"] = dataframe["ticket_text"].fillna("").astype(str).str.strip()
    dataframe["category"] = dataframe["category"].fillna("").astype(str).str.strip()

    dataframe = dataframe[(dataframe["ticket_text"] != "") & (dataframe["category"] != "")].copy()

    if dataframe.empty:
        raise ValueError("Training data contains no usable rows.")

    return dataframe


def build_model_pipeline(model_name: str) -> Pipeline:
    """
    Build a TF-IDF text-classification pipeline.

    Args:
        model_name: Model identifier.

    Returns:
        Scikit-learn pipeline containing vectorizer and classifier.

    Raises:
        ValueError: If model_name is unsupported.
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )

    if model_name == "lr":
        classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    elif model_name == "svm":
        # LinearSVC is a strong text-classification baseline, but it does not
        # provide calibrated probabilities by default. Use LogisticRegression
        # for probability-based confidence scores, or wrap SVM with
        # CalibratedClassifierCV in a future iteration.
        classifier = LinearSVC(
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    return Pipeline(
        steps=[
            ("tfidf", vectorizer),
            ("classifier", classifier),
        ]
    )


def print_dataset_summary(dataframe: pd.DataFrame) -> None:
    """
    Print basic training dataset summary.

    Args:
        dataframe: Training dataframe.
    """
    print("\nTraining dataset summary")
    print("=" * 80)
    print(f"Rows: {len(dataframe):,}")
    print("\nCategory distribution:")
    print(dataframe["category"].value_counts().to_string())

    if "source_dataset" in dataframe.columns:
        print("\nSource distribution:")
        print(dataframe["source_dataset"].value_counts().to_string())

    if "is_synthetic" in dataframe.columns:
        print("\nSynthetic distribution:")
        print(dataframe["is_synthetic"].value_counts().to_string())


def print_evaluation_results(
    *,
    y_true: pd.Series,
    y_pred: list[str],
    labels: list[str],
) -> None:
    """
    Print classification metrics and confusion matrix.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        labels: Ordered class labels.
    """
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, average="weighted")

    print("\nEvaluation metrics")
    print("=" * 80)
    print(f"accuracy:    {accuracy:.4f}")
    print(f"macro_f1:    {macro_f1:.4f}")
    print(f"weighted_f1: {weighted_f1:.4f}")

    print("\nClassification report")
    print("=" * 80)
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))

    confusion = confusion_matrix(y_true, y_pred, labels=labels)
    confusion_dataframe = pd.DataFrame(
        confusion,
        index=[f"true:{label}" for label in labels],
        columns=[f"pred:{label}" for label in labels],
    )

    print("\nConfusion matrix")
    print("=" * 80)
    print(confusion_dataframe.to_string())


def train_and_evaluate(
    *,
    dataframe: pd.DataFrame,
    model_name: str,
    output_path: Path,
) -> None:
    """
    Train and evaluate the selected model.

    Args:
        dataframe: Training dataframe.
        model_name: Model identifier.
        output_path: Path where model artifact should be saved.
    """
    x = dataframe["ticket_text"]
    y = dataframe["category"]

    labels = sorted(y.unique())

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    pipeline = build_model_pipeline(model_name)
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test).tolist()

    print_evaluation_results(
        y_true=y_test,
        y_pred=predictions,
        labels=labels,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)

    print("\nModel saved")
    print("=" * 80)
    print(f"Model type: {model_name}")
    print(f"Output path: {output_path}")


def main() -> None:
    """
    Train a category classifier from the generated training dataset.
    """
    args = parse_args()
    dataframe = load_training_data(args.training_data)

    print_dataset_summary(dataframe)
    train_and_evaluate(
        dataframe=dataframe,
        model_name=args.model,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
