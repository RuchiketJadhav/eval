"""Shared schema enumerations."""

from enum import StrEnum


class SpeakerType(StrEnum):
    """Supported conversation speaker types."""

    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class IssueSeverity(StrEnum):
    """Issue severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(StrEnum):
    """Categories used to group evaluation issues."""

    QUALITY = "quality"
    COMPLIANCE = "compliance"
    CUSTOMER_EXPERIENCE = "customer_experience"
    SYSTEM = "system"


class RecommendationType(StrEnum):
    """Recommendation action categories."""

    MODEL_RETRAIN = "model_retrain"
    HUMAN_REVIEW = "human_review"
    POLICY_UPDATE = "policy_update"
    PROMPT_UPDATE = "prompt_update"
    KNOWLEDGE_UPDATE = "knowledge_update"


class EvaluationStatus(StrEnum):
    """Lifecycle status for evaluator execution."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
