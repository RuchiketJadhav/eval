"""Evaluation context schema used by evaluator SDK implementations."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.sdk.logger import EvaluatorLogger


class EvaluationContext(BaseModel):
    """Immutable request context passed to every evaluator.

    Attributes:
        request_id: Unique identifier for the evaluation request.
        started_at: Timestamp when request processing started.
        configuration: Evaluator-agnostic runtime configuration.
        logger: Logger wrapper available to evaluators.
        trace_id: Optional distributed trace identifier.
        metadata: Additional typed caller metadata.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    request_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    configuration: dict[str, Any] = Field(default_factory=dict)
    logger: EvaluatorLogger = Field(default_factory=EvaluatorLogger)
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("request_id")
    @classmethod
    def _request_id_must_not_be_blank(cls, value: str) -> str:
        """Validate that request identifiers are not blank."""
        if not value.strip():
            msg = "request_id must not be blank"
            raise ValueError(msg)
        return value
