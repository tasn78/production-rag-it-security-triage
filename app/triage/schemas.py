"""
Shared triage schemas and enumerations.

This module defines stable domain types used by the triage classifier,
severity scorer, API layer, and tests.
"""

from dataclasses import dataclass
from enum import Enum


class TriageCategory(str, Enum):
    """
    Supported high-level categories for IT and security triage.
    """

    AUTHENTICATION = "Authentication"
    VPN_NETWORK_ACCESS = "VPN / Network Access"
    SHARED_DRIVE_ACCESS = "Shared Drive / File Access"
    WEB_SERVER = "Web Server / Nginx"
    SECURITY_ALERT = "Security Alert"
    GENERAL_IT_SUPPORT = "General IT Support"


class SeverityLevel(str, Enum):
    """
    Supported severity levels for triage output.
    """

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass(frozen=True)
class ClassificationResult:
    """
    Represents the output of ticket category classification.

    Attributes:
        category: Assigned triage category.
        matched_keywords: Keywords that contributed to the classification.
    """

    category: TriageCategory
    matched_keywords: list[str]


class ClassifierMode(str, Enum):
    """
    Supported classifier modes for category prediction.
    """

    RULE_BASED = "rule_based"
    ML = "ml"
    ML_FALLBACK_RULE_BASED = "ml_fallback_rule_based"


@dataclass(frozen=True)
class SeverityResult:
    """
    Represents the output of severity scoring.

    Attributes:
        severity: Assigned severity level.
        score: Numeric severity score used to determine the severity level.
        reasons: Human-readable reasons that contributed to the score.
    """

    severity: SeverityLevel
    score: int
    reasons: list[str]
