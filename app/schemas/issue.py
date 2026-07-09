"""Evaluation issue schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import IssueCategory, IssueSeverity


class Issue(BaseModel):
    """An issue identified by an evaluator.

    Attributes:
        id: Unique issue identifier.
        title: Short issue title.
        description: Detailed issue description.
        severity: Severity level.
        category: Issue category.
        evidence_ids: Evidence identifiers supporting the issue.
        metadata: Additional issue metadata.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "title", "description")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value
