"""Tests for core schema models."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.schemas import (
    CallMetadata,
    CompositeReport,
    Conversation,
    ConversationTurn,
    EvaluationResult,
    EvaluationStatus,
    Evidence,
    Issue,
    IssueCategory,
    IssueSeverity,
    Recommendation,
    RecommendationType,
    SpeakerType,
)
from pydantic import ValidationError


def _timestamp(offset_seconds: int = 0) -> datetime:
    """Create a stable timezone-aware timestamp."""
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset_seconds)


def _metadata() -> CallMetadata:
    """Create valid call metadata."""
    return CallMetadata(
        call_id="call-1",
        customer_id="customer-1",
        agent_id="agent-1",
        language="en-US",
        start_time=_timestamp(),
        end_time=_timestamp(60),
        duration_seconds=60,
        model_version="voice-model-1",
        channel="phone",
        custom_metadata={"region": "us"},
    )


def _turn(turn_id: str, speaker: SpeakerType, offset_seconds: int, text: str) -> ConversationTurn:
    """Create a valid conversation turn."""
    return ConversationTurn(
        turn_id=turn_id,
        speaker=speaker,
        timestamp=_timestamp(offset_seconds),
        text=text,
        intent="greeting",
        entities={"name": "example"},
        confidence=0.9,
        sentiment="neutral",
        emotion="calm",
        latency_ms=120,
    )


def _issue(severity: IssueSeverity = IssueSeverity.CRITICAL) -> Issue:
    """Create a valid issue."""
    return Issue(
        id="issue-1",
        title="Issue title",
        description="Issue description",
        severity=severity,
        category=IssueCategory.QUALITY,
        evidence_ids=("evidence-1",),
    )


def _evidence() -> Evidence:
    """Create valid evidence."""
    return Evidence(
        id="evidence-1",
        description="Evidence description",
        turn_ids=("turn-1",),
        confidence=0.8,
    )


def _recommendation() -> Recommendation:
    """Create a valid recommendation."""
    return Recommendation(
        id="recommendation-1",
        title="Recommendation title",
        description="Recommendation description",
        recommendation_type=RecommendationType.HUMAN_REVIEW,
        priority=1,
    )


def _evaluation_result(status: EvaluationStatus = EvaluationStatus.SUCCESS) -> EvaluationResult:
    """Create a valid evaluation result."""
    return EvaluationResult(
        evaluator_name="quality",
        status=status,
        score=88,
        confidence=0.95,
        execution_time_ms=15.5,
        issues=(_issue(),),
        evidence=(_evidence(),),
        recommendations=(_recommendation(),),
    )


def test_conversation_model_creation_and_computed_fields() -> None:
    """Conversation exposes computed turn counts and duration."""
    conversation = Conversation(
        metadata=_metadata(),
        turns=(
            _turn("turn-1", SpeakerType.CUSTOMER, 1, "Hello"),
            _turn("turn-2", SpeakerType.AGENT, 2, "Hi"),
            _turn("turn-3", SpeakerType.SYSTEM, 3, "System note"),
        ),
    )

    assert conversation.total_turns == 3
    assert conversation.customer_turns == 1
    assert conversation.agent_turns == 1
    assert conversation.conversation_duration == 60


def test_conversation_rejects_empty_turns() -> None:
    """Conversation cannot be empty."""
    with pytest.raises(ValidationError):
        Conversation(metadata=_metadata(), turns=())


def test_conversation_rejects_decreasing_timestamps() -> None:
    """Conversation turn timestamps must be increasing."""
    with pytest.raises(ValidationError, match="turn timestamps must be increasing"):
        Conversation(
            metadata=_metadata(),
            turns=(
                _turn("turn-2", SpeakerType.AGENT, 2, "Hi"),
                _turn("turn-1", SpeakerType.CUSTOMER, 1, "Hello"),
            ),
        )


def test_models_are_immutable() -> None:
    """Schema models prevent field reassignment."""
    turn = _turn("turn-1", SpeakerType.CUSTOMER, 1, "Hello")

    with pytest.raises(ValidationError):
        turn.text = "mutated"


def test_metadata_validation_failures() -> None:
    """Metadata rejects invalid duration, blank identifiers, and invalid time ranges."""
    with pytest.raises(ValidationError):
        CallMetadata(
            call_id="call-1",
            customer_id="customer-1",
            agent_id="agent-1",
            language="en-US",
            start_time=_timestamp(),
            end_time=_timestamp(1),
            duration_seconds=-1,
            model_version="voice-model-1",
            channel="phone",
        )

    with pytest.raises(ValidationError, match="value must not be blank"):
        CallMetadata(
            call_id=" ",
            customer_id="customer-1",
            agent_id="agent-1",
            language="en-US",
            start_time=_timestamp(),
            end_time=_timestamp(1),
            duration_seconds=1,
            model_version="voice-model-1",
            channel="phone",
        )

    with pytest.raises(ValidationError, match="end_time must be greater than or equal"):
        CallMetadata(
            call_id="call-1",
            customer_id="customer-1",
            agent_id="agent-1",
            language="en-US",
            start_time=_timestamp(2),
            end_time=_timestamp(1),
            duration_seconds=1,
            model_version="voice-model-1",
            channel="phone",
        )


def test_turn_validation_failures() -> None:
    """Turns reject blank text, invalid confidence, and negative latency."""
    with pytest.raises(ValidationError):
        _turn("turn-1", SpeakerType.CUSTOMER, 1, " ")

    with pytest.raises(ValidationError):
        ConversationTurn(
            turn_id="turn-1",
            speaker=SpeakerType.CUSTOMER,
            timestamp=_timestamp(1),
            text="Hello",
            confidence=1.1,
        )

    with pytest.raises(ValidationError):
        ConversationTurn(
            turn_id="turn-1",
            speaker=SpeakerType.CUSTOMER,
            timestamp=_timestamp(1),
            text="Hello",
            latency_ms=-1,
        )


def test_evidence_issue_and_recommendation_validation() -> None:
    """Supporting schemas validate scores, text, and priority ranges."""
    with pytest.raises(ValidationError):
        Evidence(id="evidence-1", description="Evidence", confidence=1.01)

    with pytest.raises(ValidationError):
        Issue(
            id="issue-1",
            title=" ",
            description="Description",
            severity=IssueSeverity.LOW,
            category=IssueCategory.SYSTEM,
        )

    with pytest.raises(ValidationError):
        Recommendation(
            id="recommendation-1",
            title="Title",
            description="Description",
            recommendation_type=RecommendationType.PROMPT_UPDATE,
            priority=-1,
        )


def test_evaluation_result_validation() -> None:
    """Evaluation results validate score, confidence, and execution time ranges."""
    with pytest.raises(ValidationError):
        EvaluationResult(
            evaluator_name="quality",
            status=EvaluationStatus.SUCCESS,
            score=100.1,
            confidence=0.9,
            execution_time_ms=1,
        )

    with pytest.raises(ValidationError):
        EvaluationResult(
            evaluator_name="quality",
            status=EvaluationStatus.SUCCESS,
            score=99,
            confidence=1.1,
            execution_time_ms=1,
        )

    with pytest.raises(ValidationError):
        EvaluationResult(
            evaluator_name="quality",
            status=EvaluationStatus.SUCCESS,
            score=99,
            confidence=1,
            execution_time_ms=-1,
        )


def test_composite_report_computed_fields_and_exports() -> None:
    """Composite reports expose computed counts and JSON/dict exports."""
    report = CompositeReport(
        report_id="report-1",
        conversation_id="call-1",
        overall_score=87.5,
        evaluation_results=(
            _evaluation_result(EvaluationStatus.SUCCESS),
            _evaluation_result(EvaluationStatus.FAILED),
        ),
        issues=(_issue(IssueSeverity.CRITICAL), _issue(IssueSeverity.LOW)),
        recommendations=(_recommendation(),),
        metadata={"source": "test"},
    )

    assert report.total_issues == 2
    assert report.critical_issues == 1
    assert report.failed_evaluations == 1
    assert report.to_dict()["overall_score"] == 87.5
    assert json.loads(report.to_json())["conversation_id"] == "call-1"


def test_composite_report_validation() -> None:
    """Composite reports validate identifiers and score range."""
    with pytest.raises(ValidationError):
        CompositeReport(report_id="report-1", conversation_id="call-1", overall_score=101)

    with pytest.raises(ValidationError, match="value must not be blank"):
        CompositeReport(report_id=" ", conversation_id="call-1")


def test_conversation_json_export_includes_computed_fields() -> None:
    """Conversation JSON export includes serialized turns and computed fields."""
    conversation = Conversation(
        metadata=_metadata(),
        turns=(
            _turn("turn-1", SpeakerType.CUSTOMER, 1, "Hello"),
            _turn("turn-2", SpeakerType.AGENT, 2, "Hi"),
        ),
    )

    payload = json.loads(conversation.model_dump_json())

    assert payload["metadata"]["call_id"] == "call-1"
    assert payload["turns"][0]["speaker"] == "customer"
    assert payload["total_turns"] == 2
    assert payload["customer_turns"] == 1
    assert payload["agent_turns"] == 1


def test_enum_validation() -> None:
    """Enums validate known values and reject unknown values."""
    customer_speaker: Any = "customer"
    invalid_speaker: Any = "supervisor"

    assert (
        ConversationTurn(
            turn_id="turn-1",
            speaker=customer_speaker,
    assert (
        ConversationTurn(
            turn_id="turn-1",
            speaker="customer",
            timestamp=_timestamp(1),
            text="Hello",
        ).speaker
        is SpeakerType.CUSTOMER
    )

    with pytest.raises(ValidationError):
        ConversationTurn(
            turn_id="turn-1",
            speaker=invalid_speaker,
            speaker="supervisor",
            timestamp=_timestamp(1),
            text="Hello",
        )
