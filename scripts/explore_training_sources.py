"""
Explore raw ticket datasets before ML training.

This script inspects candidate public support-ticket datasets, applies early
mapping rules to the project's target triage categories, and prints class
distributions plus sample text examples for manual review.

Raw datasets are expected to be stored locally under data/raw/ and are not
committed to Git.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Combined dataset training preview path
MAPPED_TRAINING_PREVIEW_PATH = RAW_DATA_DIR.parent / "training" / "mapped_training_preview.csv"

KAGGLE_IT_SUPPORT_PATH = RAW_DATA_DIR / "kaggle_it_support_tickets.csv"
MENDELEY_ISSUES_PATH = RAW_DATA_DIR / "mendeley_issues.csv"
MENDELEY_UTTERANCES_PATH = RAW_DATA_DIR / "mendeley_sample_utterances.csv"

TARGET_CATEGORIES = (
    "Security Alert",
    "VPN / Network Access",
    "Shared Drive / File Access",
    "Authentication",
    "Web Server / Nginx",
    "General IT Support",
)

LOW_VALUE_TEXT = {
    "",
    ".",
    "-",
    "greetings",
    "thank you",
    "thanks",
    "best regards",
    "regards",
    "dear team",
    "hello",
    "hi",
}


def build_training_preview_rows(
    *,
    dataframe: pd.DataFrame,
    source_dataset: str,
    text_column: str,
    source_label_column: str | None,
    priority_column: str | None,
) -> pd.DataFrame:
    """
    Build standardized mapped training preview rows.

    Args:
        dataframe: Source dataframe with normalized and mapped text.
        source_dataset: Name of the source dataset.
        text_column: Column containing original ticket text.
        source_label_column: Optional source label column.
        priority_column: Optional priority/severity column.

    Returns:
        Standardized preview dataframe.
    """
    useful_rows = dataframe[dataframe["has_useful_text"]].copy()

    source_label = (
        useful_rows[source_label_column]
        if source_label_column and source_label_column in useful_rows.columns
        else ""
    )
    priority = (
        useful_rows[priority_column]
        if priority_column and priority_column in useful_rows.columns
        else ""
    )

    preview = pd.DataFrame(
        {
            "source_dataset": source_dataset,
            "source_label": source_label,
            "ticket_text": useful_rows[text_column],
            "mapped_target_category": useful_rows["mapped_target_category"],
            "priority": priority,
            "is_synthetic": False,
        }
    )

    return preview


def normalize_text(value: object) -> str:
    """
    Normalize text values for inspection and keyword matching.

    Args:
        value: Raw value from a dataframe cell.

    Returns:
        Lowercase text with repeated whitespace collapsed.
    """
    if pd.isna(value):
        return ""

    return " ".join(str(value).strip().lower().split())


def has_useful_text(text: str, minimum_length: int = 25) -> bool:
    """
    Determine whether text is likely useful for NLP training.

    Args:
        text: Normalized text.
        minimum_length: Minimum character length required.

    Returns:
        True if the text appears useful, otherwise False.
    """
    if len(text) < minimum_length:
        return False

    if text in LOW_VALUE_TEXT:
        return False

    placeholder_tokens = (
        "ph_user",
        "ph_name",
        "ph_file",
        "ph_technical",
        "ph_log",
        "ph_code",
        "ph_sql",
        "ph_path",
    )
    placeholder_count = sum(text.count(token) for token in placeholder_tokens)
    token_count = max(len(text.split()), 1)

    return placeholder_count / token_count <= 0.4


def map_text_to_target_category(text: str) -> str:
    """
    Map ticket text to one of the project's target categories.

    These rules are intentionally conservative for data exploration. They are
    not the final ML model.

    Args:
        text: Normalized ticket text.

    Returns:
        Mapped target category.
    """
    security_keywords = (
        "brute force",
        "brute force attack",
        "password spraying",
        "credential stuffing",
        "unauthorized",
        "malware",
        "phishing",
        "cyber threat",
        "security threat",
        "ddos attack",
        "ransomware attack",
        "under attack",
        "system compromise",
        "account compromise",
        "credential compromise",
        "obtained passwords",
        "stolen passwords",
        "vulnerability",
        "vulnerabilities",
        "exploit",
        "security breach",
        "security incident",
        "security alert",
        "security vulnerability",
        "security vulnerabilities",
        "firewall",
        "blocked ip",
        "external ip",
        "tls",
        "ssl",
        "cipher",
        "http trace",
        "beast attack",
        "ssl certificate",
        "tls certificate",
        "expired certificate",
        "certificate error",
        "certificate expired",
        "data encryption",
        "disk encryption",
    )
    vpn_network_keywords = (
        "vpn",
        "vpn connection",
        "remote access",
        "network outage",
        "network failure",
        "network issue",
        "network problem",
        "network access",
        "network connectivity",
        "network configuration",
        "network connection lost",
        "network connection failed",
        "dns",
        "default gateway",
        "network gateway",
        "internal resources",
        "internal system",
        "cannot connect",
        "can't connect",
        "unable to connect",
    )
    shared_drive_keywords = (
        "shared drive",
        "mapped drive",
        "network drive",
        "file share",
        "folder permission",
        "shared folder",
        "access denied",
        "unc path",
    )
    authentication_keywords = (
        "password",
        "password reset",
        "forgot password",
        "forgotten password",
        "account locked",
        "account lockout",
        "locked out",
        "mfa",
        "multi-factor",
        "authentication",
        "login",
        "sign in",
        "credentials",
    )
    web_server_keywords = (
        "nginx",
        "apache web server",
        "apache http",
        "apache nginx",
        "tomcat",
        "iis",
        "web server",
        "web servers",
        "web server configuration",
        "nginx configuration",
        "apache configuration",
        "tomcat configuration",
        "http rate limit",
        "nginx rate limit",
        "api rate limit exceeded",
        "server error",
        "reverse proxy",
        "http 401",
        "http 403",
        "http 404",
        "http 429",
        "http 500",
        "502 bad gateway",
        "bad gateway",
        "http trace",
        "disable http",
        "configure https",
        "http method",
        "https configured",
        "http enabled",
    )

    if any(keyword in text for keyword in security_keywords):
        return "Security Alert"

    if any(keyword in text for keyword in vpn_network_keywords):
        return "VPN / Network Access"

    if any(keyword in text for keyword in shared_drive_keywords):
        return "Shared Drive / File Access"

    if any(keyword in text for keyword in authentication_keywords):
        return "Authentication"

    if any(keyword in text for keyword in web_server_keywords):
        return "Web Server / Nginx"

    return "General IT Support"


def print_header(title: str) -> None:
    """
    Print a section header.

    Args:
        title: Header title.
    """
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_value_counts(
    dataframe: pd.DataFrame,
    column_name: str,
    title: str,
    limit: int = 20,
) -> None:
    """
    Print value counts for a dataframe column when present.

    Args:
        dataframe: Source dataframe.
        column_name: Column to summarize.
        title: Display title.
        limit: Maximum number of values to print.
    """
    if column_name not in dataframe.columns:
        print(f"{title}: column not found ({column_name})")
        return

    print(f"\n{title}")
    print(dataframe[column_name].value_counts(dropna=False).head(limit).to_string())


def print_category_samples(
    dataframe: pd.DataFrame,
    text_column: str,
    category_column: str,
    samples_per_category: int = 5,
) -> None:
    """
    Print sample mapped examples for manual label sanity checks.

    Args:
        dataframe: Source dataframe.
        text_column: Column containing display text.
        category_column: Column containing mapped target category.
        samples_per_category: Number of examples to print per category.
    """
    print_header("Sample Text by Mapped Target Category")

    for category in TARGET_CATEGORIES:
        category_rows = dataframe[dataframe[category_column] == category]

        print(f"\n--- {category} ({len(category_rows)} rows) ---")

        if category_rows.empty:
            print("No mapped examples.")
            continue

        samples = category_rows[text_column].dropna().head(samples_per_category)

        for index, sample in enumerate(samples, start=1):
            clean_sample = " ".join(str(sample).split())
            print(f"{index}. {clean_sample[:500]}")


def load_csv_if_exists(path: Path) -> pd.DataFrame | None:
    """
    Load a CSV file if it exists.

    Args:
        path: CSV path.

    Returns:
        Loaded dataframe, or None if missing.
    """
    if not path.exists():
        print(f"Missing file: {path}")
        return None

    return pd.read_csv(path)


def explore_kaggle_it_support() -> pd.DataFrame | None:
    """
    Explore the Kaggle IT support ticket dataset.

    Returns:
        Dataframe with normalized text and mapped target category, if available.
    """
    print_header("Kaggle IT Support Ticket Data")

    dataframe = load_csv_if_exists(KAGGLE_IT_SUPPORT_PATH)

    if dataframe is None:
        return None

    print(f"Rows: {len(dataframe):,}")
    print(f"Columns: {list(dataframe.columns)}")

    text_column = "Body"
    if text_column not in dataframe.columns:
        print(f"Expected text column not found: {text_column}")
        return dataframe

    dataframe["normalized_text"] = dataframe[text_column].map(normalize_text)
    dataframe["has_useful_text"] = dataframe["normalized_text"].map(has_useful_text)
    dataframe["mapped_target_category"] = dataframe["normalized_text"].map(
        map_text_to_target_category
    )

    print(f"Missing text rows: {(dataframe['normalized_text'] == '').sum():,}")
    print(f"Useful text rows: {dataframe['has_useful_text'].sum():,}")

    print_value_counts(dataframe, "Department", "Original Department Distribution")
    print_value_counts(dataframe, "Priority", "Original Priority Distribution")
    print_value_counts(dataframe, "Tags", "Top Tags", limit=10)
    print_value_counts(
        dataframe,
        "mapped_target_category",
        "Mapped Target Category Distribution",
    )

    useful_rows = dataframe[dataframe["has_useful_text"]].copy()
    print_category_samples(
        dataframe=useful_rows,
        text_column=text_column,
        category_column="mapped_target_category",
    )

    return dataframe


def explore_mendeley_issues() -> pd.DataFrame | None:
    """
    Explore the Mendeley help desk issues dataset.

    Returns:
        Loaded dataframe, if available.
    """
    print_header("Mendeley Help Desk Issues")

    dataframe = load_csv_if_exists(MENDELEY_ISSUES_PATH)

    if dataframe is None:
        return None

    print(f"Rows: {len(dataframe):,}")
    print(f"Columns: {list(dataframe.columns)}")

    for column_name in (
        "issue_type",
        "issue_priority",
        "issue_resolution",
        "issue_status",
        "issue_comments_count",
        "processing_steps",
    ):
        print_value_counts(
            dataframe=dataframe,
            column_name=column_name,
            title=f"{column_name} Distribution",
        )

    return dataframe


def explore_mendeley_utterances() -> pd.DataFrame | None:
    """
    Explore public reporter utterances from the Mendeley help desk dataset.

    Returns:
        Dataframe with normalized text and mapped target category, if available.
    """
    print_header("Mendeley Help Desk Sample Utterances")

    dataframe = load_csv_if_exists(MENDELEY_UTTERANCES_PATH)

    if dataframe is None:
        return None

    print(f"Rows: {len(dataframe):,}")
    print(f"Columns: {list(dataframe.columns)}")

    if "actionbody" not in dataframe.columns:
        print("Expected text column not found: actionbody")
        return dataframe

    dataframe["normalized_text"] = dataframe["actionbody"].map(normalize_text)

    reporter_public_rows = dataframe.copy()

    if "author_role" in reporter_public_rows.columns:
        reporter_public_rows = reporter_public_rows[
            reporter_public_rows["author_role"].map(normalize_text) == "reporter"
        ]

    if "is_private" in reporter_public_rows.columns:
        reporter_public_rows = reporter_public_rows[
            reporter_public_rows["is_private"].fillna(1).astype(float) == 0.0
        ]

    reporter_public_rows = reporter_public_rows.copy()
    reporter_public_rows["has_useful_text"] = reporter_public_rows["normalized_text"].map(
        has_useful_text
    )
    reporter_public_rows["mapped_target_category"] = reporter_public_rows["normalized_text"].map(
        map_text_to_target_category
    )

    useful_rows = reporter_public_rows[reporter_public_rows["has_useful_text"]].copy()

    print_value_counts(dataframe, "author_role", "Author Role Distribution")
    print_value_counts(dataframe, "is_private", "Private/Public Distribution")

    print(f"\nReporter public rows: {len(reporter_public_rows):,}")
    print(f"Useful reporter public rows: {len(useful_rows):,}")

    print_value_counts(
        useful_rows,
        "mapped_target_category",
        "Mapped Target Category Distribution",
    )

    print_category_samples(
        dataframe=useful_rows,
        text_column="actionbody",
        category_column="mapped_target_category",
    )

    return reporter_public_rows


def main() -> None:
    """
    Run all available dataset exploration steps and export mapped preview rows.
    """
    print_header("ML Training Source Exploration")
    print(f"Raw data directory: {RAW_DATA_DIR}")

    preview_dataframes = []

    kaggle_dataframe = explore_kaggle_it_support()
    if kaggle_dataframe is not None and "has_useful_text" in kaggle_dataframe.columns:
        preview_dataframes.append(
            build_training_preview_rows(
                dataframe=kaggle_dataframe,
                source_dataset="kaggle_it_support",
                text_column="Body",
                source_label_column="Department",
                priority_column="Priority",
            )
        )

    explore_mendeley_issues()

    mendeley_utterances_dataframe = explore_mendeley_utterances()
    if (
        mendeley_utterances_dataframe is not None
        and "has_useful_text" in mendeley_utterances_dataframe.columns
    ):
        preview_dataframes.append(
            build_training_preview_rows(
                dataframe=mendeley_utterances_dataframe,
                source_dataset="mendeley_reporter_utterances",
                text_column="actionbody",
                source_label_column="author_role",
                priority_column=None,
            )
        )

    if preview_dataframes:
        preview = pd.concat(preview_dataframes, ignore_index=True)
        MAPPED_TRAINING_PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        preview.to_csv(MAPPED_TRAINING_PREVIEW_PATH, index=False)

        print_header("Mapped Training Preview Export")
        print(f"Rows exported: {len(preview):,}")
        print(f"Output path: {MAPPED_TRAINING_PREVIEW_PATH}")


if __name__ == "__main__":
    main()
