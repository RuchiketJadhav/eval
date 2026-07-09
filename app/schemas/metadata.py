"""Call metadata schema."""

from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CallMetadata(BaseModel):
    """Metadata that identifies and describes an evaluated call.

    Attributes:
        call_id: Unique identifier for the call.
        customer_id: Unique identifier for the customer.
        agent_id: Unique identifier for the agent or agent instance.
        language: BCP-47 language tag or internal language code.
        start_time: Call start timestamp.
        end_time: Call end timestamp.
        duration_seconds: Non-negative call duration in seconds.
        model_version: Version of the AI model used during the call.
        channel: Source channel for the conversation.
        custom_metadata: Additional integration-specific metadata.
    """

    model_config = ConfigDict(frozen=True)

    call_id: str
    customer_id: str
    agent_id: str
    language: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float = Field(ge=0)
    model_version: str
    channel: str
    custom_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("call_id", "customer_id", "agent_id", "language", "model_version", "channel")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_time_range(self) -> Self:
        """Validate that end time is not earlier than start time."""
        if self.end_time < self.start_time:
            msg = "end_time must be greater than or equal to start_time"
            raise ValueError(msg)
        return self
