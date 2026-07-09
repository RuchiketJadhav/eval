"""Evaluator result schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import EvaluationStatus
from app.schemas.evidence import Evidence
from app.schemas.issue import Issue
from app.schemas.recommendation import Recommendation


class EvaluationResult(BaseModel):
    """Structured result returned by every evaluator.

    Attributes:
        evaluator_name: Name of the evaluator that produced the result.
        status: Evaluator execution status.
        score: Optional score between 0 and 100.
        confidence: Confidence score between 0 and 1.
        execution_time_ms: Non-negative execution time in milliseconds.
        issues: Issues identified by the evaluator.
        evidence: Evidence supporting scores and issues.
        recommendations: Recommended follow-up actions.
        metadata: Additional evaluator metadata.
    """

    model_config = ConfigDict(frozen=True)

    evaluator_name: str
    status: EvaluationStatus
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    execution_time_ms: float = Field(ge=0)
    issues: tuple[Issue, ...] = Field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = Field(default_factory=tuple)
    recommendations: tuple[Recommendation, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("evaluator_name")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that evaluator name is not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value
