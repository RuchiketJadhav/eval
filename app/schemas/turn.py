"""Conversation turn schema."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import SpeakerType


class ConversationTurn(BaseModel):
    """A single immutable turn in a conversation.

    Attributes:
        turn_id: Unique turn identifier within a conversation.
        speaker: Speaker responsible for the turn.
        timestamp: Timestamp when the turn occurred.
        text: Transcript text for the turn.
        intent: Optional detected intent.
        entities: Extracted entities for the turn.
        confidence: Optional confidence score between 0 and 1.
        sentiment: Optional sentiment label.
        emotion: Optional emotion label.
        latency_ms: Optional non-negative response latency in milliseconds.
    """

    model_config = ConfigDict(frozen=True)

    turn_id: str
    speaker: SpeakerType
    timestamp: datetime
    text: str
    intent: str | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    sentiment: str | None = None
    emotion: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)

    @field_validator("turn_id", "text")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Validate that required string fields are not blank."""
        if not value.strip():
            msg = "value must not be blank"
            raise ValueError(msg)
        return value
