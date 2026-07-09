"""Tests for evaluator SDK primitives."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.schemas import (
    CallMetadata,
    Conversation,
    ConversationTurn,
    EvaluationResult,
    EvaluationStatus,
    SpeakerType,
)
from app.sdk import (
    BaseEvaluator,
    EvaluationContext,
    EvaluationException,
    EvaluationTimeoutException,
    EvaluationTimer,
    EvaluatorConfigurationException,
    EvaluatorLogger,
    InvalidConversationException,
    clamp_score,
    confidence_average,
    normalize_score,
    weighted_average,
)
from pydantic import ValidationError


def _timestamp(offset_seconds: int = 0) -> datetime:
    """Create a stable timestamp."""
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset_seconds)


def _conversation() -> Conversation:
    """Create a valid conversation for SDK tests."""
    metadata = CallMetadata(
        call_id="call-1",
        customer_id="customer-1",
        agent_id="agent-1",
        language="en-US",
        start_time=_timestamp(),
        end_time=_timestamp(5),
        duration_seconds=5,
        model_version="model-1",
        channel="phone",
    )
    return Conversation(
        metadata=metadata,
        turns=(
            ConversationTurn(
                turn_id="turn-1",
                speaker=SpeakerType.CUSTOMER,
                timestamp=_timestamp(1),
                text="Hello",
            ),
        ),
    )


class ConcreteEvaluator(BaseEvaluator):
    """Concrete evaluator used to test the abstract SDK contract."""

    async def evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Return a deterministic evaluator result for tests."""
        await self.before_evaluate(conversation, context)
        result = EvaluationResult(
            evaluator_name=self.evaluator_name,
            status=EvaluationStatus.SUCCESS,
            score=100,
            confidence=1,
            execution_time_ms=1,
        )
        await self.after_evaluate(conversation, context, result)
        return result


def test_base_evaluator_is_abstract() -> None:
    """The base evaluator cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseEvaluator()  # type: ignore[abstract]


def test_base_evaluator_metadata_and_evaluate_contract() -> None:
    """Concrete evaluators expose metadata and return typed results."""
    evaluator = ConcreteEvaluator(evaluator_name="quality", version="1.2.3")
    context = EvaluationContext(request_id="request-1")

    result = asyncio.run(evaluator.evaluate(_conversation(), context))

    assert evaluator.evaluator_name == "quality"
    assert evaluator.version == "1.2.3"
    assert isinstance(result, EvaluationResult)
    assert result.evaluator_name == "quality"


def test_base_evaluator_lifecycle_hooks_are_async_ready() -> None:
    """Lifecycle hooks can be awaited by future orchestrator code."""
    evaluator = ConcreteEvaluator()
    context = EvaluationContext(request_id="request-1")
    conversation = _conversation()

    async def run_hooks() -> None:
        await evaluator.initialize(context)
        await evaluator.before_evaluate(conversation, context)
        result = await evaluator.evaluate(conversation, context)
        await evaluator.after_evaluate(conversation, context, result)
        await evaluator.shutdown(context)

    asyncio.run(run_hooks())


def test_validate_input_rejects_empty_conversation_like_objects() -> None:
    """Generic validation raises the SDK invalid conversation exception."""
    evaluator = ConcreteEvaluator()
    context = EvaluationContext(request_id="request-1")
    conversation = _conversation().model_copy(update={"turns": ()})

    with pytest.raises(InvalidConversationException):
        evaluator.validate_input(conversation, context)


def test_evaluation_context_defaults_and_validation() -> None:
    """EvaluationContext is immutable and validates request identifiers."""
    context = EvaluationContext(
        request_id="request-1",
        configuration={"threshold": 0.9},
        trace_id="trace-1",
        metadata={"tenant": "tenant-1"},
    )

    assert context.request_id == "request-1"
    assert context.configuration["threshold"] == 0.9
    assert isinstance(context.logger, EvaluatorLogger)
    assert context.trace_id == "trace-1"

    with pytest.raises(ValidationError):
        context.request_id = "mutated"

    with pytest.raises(ValidationError, match="request_id must not be blank"):
        EvaluationContext(request_id=" ")


def test_evaluator_logger_methods_delegate_without_error() -> None:
    """EvaluatorLogger exposes expected log-level helper methods."""
    logger = EvaluatorLogger("test-evaluator").bind(request_id="request-1")

    logger.debug("debug-event", value=1)
    logger.info("info-event", value=1)
    logger.warning("warning-event", value=1)
    logger.error("error-event", value=1)


def test_evaluation_timer_measures_elapsed_time() -> None:
    """EvaluationTimer records elapsed milliseconds as an async context manager."""

    async def run_timer() -> float:
        async with EvaluationTimer() as timer:
            await asyncio.sleep(0)
        return timer.elapsed_ms

    elapsed_ms = asyncio.run(run_timer())

    assert elapsed_ms >= 0


def test_evaluation_timer_before_start_is_zero() -> None:
    """Inactive timers report zero elapsed milliseconds."""
    assert EvaluationTimer().elapsed_ms == 0


def test_clamp_score() -> None:
    """Score clamping respects inclusive bounds."""
    assert clamp_score(110) == 100
    assert clamp_score(-10) == 0
    assert clamp_score(50) == 50

    with pytest.raises(ValueError, match="minimum cannot be greater than maximum"):
        clamp_score(50, minimum=100, maximum=0)


def test_normalize_score() -> None:
    """Score normalization maps source values to target ranges."""
    assert normalize_score(5, 0, 10) == 50
    assert normalize_score(15, 0, 10) == 100
    assert normalize_score(-5, 0, 10) == 0
    assert normalize_score(0.5, 0, 1, 0, 1) == 0.5

    with pytest.raises(ValueError, match="source range cannot be zero"):
        normalize_score(1, 1, 1)

    with pytest.raises(ValueError, match="target_minimum cannot be greater"):
        normalize_score(1, 0, 2, 10, 0)


def test_weighted_average() -> None:
    """Weighted average handles empty input and validates weights."""
    assert weighted_average([]) == 0
    assert weighted_average([(80, 2), (100, 1)]) == pytest.approx(86.6666667)

    with pytest.raises(ValueError, match="weights cannot be negative"):
        weighted_average([(80, -1)])

    with pytest.raises(ValueError, match="total weight must be greater than zero"):
        weighted_average([(80, 0)])


def test_confidence_average() -> None:
    """Confidence averaging validates the inclusive 0 to 1 range."""
    assert confidence_average([]) == 0
    assert confidence_average([0.5, 1.0]) == 0.75

    with pytest.raises(ValueError, match="confidence values must be between 0 and 1"):
        confidence_average([0.5, 1.1])


def test_exception_hierarchy() -> None:
    """SDK exceptions inherit from the base evaluation exception."""
    assert issubclass(InvalidConversationException, EvaluationException)
    assert issubclass(EvaluationTimeoutException, EvaluationException)
    assert issubclass(EvaluatorConfigurationException, EvaluationException)
