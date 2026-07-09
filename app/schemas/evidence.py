"""Evaluation evidence schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Evidence(BaseModel):
    """Supporting evidence explaining why an evaluator produced a result.

    Attributes:
        id: Unique evidence identifier.
        description: Human-readable evidence description.
        turn_ids: Related conversation turn identifiers.
        confidence: Confidence score between 0 and 1.
        metadata: Additional evidence metadata.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    description: str
    turn_ids: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "description")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value
