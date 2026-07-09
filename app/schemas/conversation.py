"""Conversation schema."""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, model_validator

from app.schemas.enums import SpeakerType
from app.schemas.metadata import CallMetadata
from app.schemas.turn import ConversationTurn


class Conversation(BaseModel):
    """Immutable representation of an entire evaluated conversation.

    Attributes:
        metadata: Call-level metadata.
        turns: Ordered conversation turns with increasing timestamps.
    """

    model_config = ConfigDict(frozen=True)

    metadata: CallMetadata
    turns: tuple[ConversationTurn, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_turn_order(self) -> Self:
        """Validate that turn timestamps are monotonically increasing."""
        timestamps = [turn.timestamp for turn in self.turns]
        if timestamps != sorted(timestamps):
            msg = "turn timestamps must be increasing"
            raise ValueError(msg)
        return self

    @computed_field
    @property
    def total_turns(self) -> int:
        """Return the total number of turns."""
        return len(self.turns)

    @computed_field
    @property
    def customer_turns(self) -> int:
        """Return the number of customer turns."""
        return self._count_turns_by_speaker(SpeakerType.CUSTOMER)

    @computed_field
    @property
    def agent_turns(self) -> int:
        """Return the number of agent turns."""
        return self._count_turns_by_speaker(SpeakerType.AGENT)

    @computed_field
    @property
    def conversation_duration(self) -> float:
        """Return the metadata duration in seconds."""
        return self.metadata.duration_seconds

    @field_serializer("turns")
    def _serialize_turns(self, turns: tuple[ConversationTurn, ...]) -> list[dict[str, Any]]:
        """Serialize immutable turn storage as a JSON-compatible list."""
        return [turn.model_dump(mode="json") for turn in turns]

    def _count_turns_by_speaker(self, speaker: SpeakerType) -> int:
        """Count turns for a speaker type."""
        return sum(1 for turn in self.turns if turn.speaker == speaker)
