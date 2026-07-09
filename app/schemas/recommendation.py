"""Evaluation recommendation schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import RecommendationType


class Recommendation(BaseModel):
    """A recommended follow-up action produced by an evaluator or report.

    Attributes:
        id: Unique recommendation identifier.
        title: Short recommendation title.
        description: Detailed recommendation description.
        recommendation_type: Recommended action type.
        priority: Non-negative priority where lower values can be handled by callers.
        metadata: Additional recommendation metadata.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "title", "description")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value
