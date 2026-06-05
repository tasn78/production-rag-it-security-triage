"""
Build a local ML training dataset for ticket category classification.

This script combines mapped public support-ticket examples with curated
synthetic examples, applies per-category caps to reduce class imbalance, and
exports a local training CSV.

Generated outputs are written under data/training/ and are not committed to Git.
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MAPPED_PREVIEW_PATH = PROJECT_ROOT / "data" / "training" / "mapped_training_preview.csv"
CURATED_EXAMPLES_PATH = PROJECT_ROOT / "data" / "curated" / "curated_training_examples.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "training" / "category_training_set.csv"

MAX_EXAMPLES_PER_CATEGORY = 800
RANDOM_STATE = 42

OUTPUT_COLUMNS = [
    "ticket_text",
    "category",
    "severity",
    "source_dataset",
    "is_synthetic",
]


def load_mapped_preview(path: Path) -> pd.DataFrame:
    """
    Load mapped public dataset preview rows.

    Args:
        path: Path to mapped_training_preview.csv.

    Returns:
        Standardized dataframe for model training.

    Raises:
        FileNotFoundError: If the mapped preview file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Mapped training preview not found: {path}. "
            "Run python -m scripts.explore_training_sources first."
        )

    dataframe = pd.read_csv(path)

    required_columns = {
        "ticket_text",
        "mapped_target_category",
        "priority",
        "source_dataset",
        "is_synthetic",
    }
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(f"Mapped preview is missing columns: {sorted(missing_columns)}")

    standardized = pd.DataFrame(
        {
            "ticket_text": dataframe["ticket_text"],
            "category": dataframe["mapped_target_category"],
            "severity": dataframe["priority"].fillna("unknown"),
            "source_dataset": dataframe["source_dataset"],
            "is_synthetic": dataframe["is_synthetic"].astype(bool),
        }
    )

    return standardized


def load_curated_examples(path: Path) -> pd.DataFrame:
    """
    Load curated synthetic JSONL examples.

    Args:
        path: Path to curated_training_examples.jsonl.

    Returns:
        Standardized dataframe for model training.

    Raises:
        FileNotFoundError: If the curated examples file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Curated training examples not found: {path}")

    records = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}") from error

        records.append(record)

    dataframe = pd.DataFrame(records)

    required_columns = {
        "ticket_text",
        "category",
        "severity",
        "source",
        "is_synthetic",
    }
    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(f"Curated examples are missing columns: {sorted(missing_columns)}")

    standardized = pd.DataFrame(
        {
            "ticket_text": dataframe["ticket_text"],
            "category": dataframe["category"],
            "severity": dataframe["severity"],
            "source_dataset": dataframe["source"],
            "is_synthetic": dataframe["is_synthetic"].astype(bool),
        }
    )

    return standardized


def clean_training_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and deduplicate training rows.

    Args:
        dataframe: Combined training dataframe.

    Returns:
        Cleaned dataframe.
    """
    cleaned = dataframe.copy()

    cleaned["ticket_text"] = cleaned["ticket_text"].fillna("").astype(str).str.strip()
    cleaned["category"] = cleaned["category"].fillna("").astype(str).str.strip()
    cleaned["severity"] = cleaned["severity"].fillna("unknown").astype(str).str.strip().str.lower()
    cleaned["source_dataset"] = cleaned["source_dataset"].fillna("unknown").astype(str).str.strip()
    cleaned["is_synthetic"] = cleaned["is_synthetic"].astype(bool)

    cleaned = cleaned[(cleaned["ticket_text"] != "") & (cleaned["category"] != "")].copy()

    cleaned = cleaned.drop_duplicates(subset=["ticket_text", "category"])
    cleaned = cleaned[OUTPUT_COLUMNS]

    return cleaned


def cap_examples_per_category(
    dataframe: pd.DataFrame,
    max_examples_per_category: int,
) -> pd.DataFrame:
    """
    Shuffle and cap examples per category.

    Args:
        dataframe: Cleaned training dataframe.
        max_examples_per_category: Maximum examples to retain per category.

    Returns:
        Capped dataframe.
    """
    capped_groups = []

    for _category, group in dataframe.groupby("category", sort=True):
        shuffled_group = group.sample(frac=1.0, random_state=RANDOM_STATE)

        if len(shuffled_group) > max_examples_per_category:
            shuffled_group = shuffled_group.head(max_examples_per_category)

        capped_groups.append(shuffled_group)

    capped = pd.concat(capped_groups, ignore_index=True)
    capped = capped.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)

    return capped


def print_distribution(dataframe: pd.DataFrame, column_name: str, title: str) -> None:
    """
    Print a value-count distribution.

    Args:
        dataframe: Dataframe to summarize.
        column_name: Column to count.
        title: Printed section title.
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(dataframe[column_name].value_counts(dropna=False).to_string())


def main() -> None:
    """
    Build and export the category training dataset.
    """
    mapped_preview = load_mapped_preview(MAPPED_PREVIEW_PATH)
    curated_examples = load_curated_examples(CURATED_EXAMPLES_PATH)

    combined = pd.concat([mapped_preview, curated_examples], ignore_index=True)
    cleaned = clean_training_rows(combined)
    capped = cap_examples_per_category(
        dataframe=cleaned,
        max_examples_per_category=MAX_EXAMPLES_PER_CATEGORY,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    capped.to_csv(OUTPUT_PATH, index=False)

    print("\nBuilt category training dataset")
    print(f"Input rows before cleaning: {len(combined):,}")
    print(f"Rows after cleaning/deduplication: {len(cleaned):,}")
    print(f"Rows after per-category capping: {len(capped):,}")
    print(f"Max examples per category: {MAX_EXAMPLES_PER_CATEGORY:,}")
    print(f"Output path: {OUTPUT_PATH}")

    print_distribution(capped, "category", "Category Distribution")
    print_distribution(capped, "source_dataset", "Source Dataset Distribution")
    print_distribution(capped, "is_synthetic", "Synthetic Flag Distribution")
    print_distribution(capped, "severity", "Severity Distribution")


if __name__ == "__main__":
    main()
