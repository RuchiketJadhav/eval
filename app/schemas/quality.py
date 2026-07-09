"""Quality evaluation report schemas for the MVP web application."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QualityIssueSeverity(StrEnum):
    """Severity levels returned for quality issues."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationPriority(StrEnum):
    """Priority levels returned for quality recommendations."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class QualityIssue(BaseModel):
    """Issue identified during quality evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: QualityIssueSeverity
    title: str
    description: str
    evidence: str


class QualityRecommendation(BaseModel):
    """Recommendation identified during quality evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    priority: RecommendationPriority
    title: str
    description: str


class QualityEvaluationReport(BaseModel):
    """Structured JSON object returned by the Quality Evaluator."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    overall_score: float = Field(ge=0, le=100)
    intent_score: float = Field(ge=0, le=100)
    response_score: float = Field(ge=0, le=100)
    context_score: float = Field(ge=0, le=100)
    flow_score: float = Field(ge=0, le=100)
    completion_score: float = Field(ge=0, le=100)
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    issues: list[QualityIssue]
    recommendations: list[QualityRecommendation]

    @field_validator("summary")
    @classmethod
    def _summary_must_not_be_blank(cls, value: str) -> str:
        """Validate summary content."""
        if not value.strip():
            raise ValueError("summary must not be blank")
        return value
