"""Composite evaluation report schema."""

from datetime import UTC, datetime
from typing import Any
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.schemas.enums import EvaluationStatus, IssueSeverity
from app.schemas.evaluation import EvaluationResult
from app.schemas.issue import Issue
from app.schemas.recommendation import Recommendation


class CompositeReport(BaseModel):
    """Final composite report returned by the evaluation engine.

    Attributes:
        report_id: Unique report identifier.
        conversation_id: Identifier of the evaluated conversation.
        created_at: Timestamp when the report was created.
        overall_score: Optional aggregate score between 0 and 100.
        evaluation_results: Evaluator results included in the report.
        issues: Aggregated report issues.
        recommendations: Aggregated report recommendations.
        metadata: Additional report metadata.
    """

    model_config = ConfigDict(frozen=True)

    report_id: str
    conversation_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    overall_score: float | None = Field(default=None, ge=0, le=100)
    evaluation_results: tuple[EvaluationResult, ...] = Field(default_factory=tuple)
    issues: tuple[Issue, ...] = Field(default_factory=tuple)
    recommendations: tuple[Recommendation, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("report_id", "conversation_id")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value

    @computed_field
    @property
    def total_issues(self) -> int:
        """Return the total number of report issues."""
        return len(self.issues)

    @computed_field
    @property
    def critical_issues(self) -> int:
        """Return the number of critical report issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL)

    @computed_field
    @property
    def failed_evaluations(self) -> int:
        """Return the number of failed evaluator results."""
        return sum(
            1 for result in self.evaluation_results if result.status == EvaluationStatus.FAILED
        )

    def to_json(self) -> str:
        """Serialize the report to JSON."""
        return self.model_dump_json()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a dictionary."""
        return self.model_dump(mode="json")
        return cast(str, self.model_dump_json())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a dictionary."""
        return cast(dict[str, Any], self.model_dump(mode="json"))
