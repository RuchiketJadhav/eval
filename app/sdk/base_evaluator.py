"""Abstract base class for all evaluators."""

from abc import ABC, abstractmethod

from app.schemas import Conversation, EvaluationResult
from app.sdk.context import EvaluationContext
from app.sdk.exceptions import InvalidConversationException


class BaseEvaluator(ABC):
    """Async-ready contract implemented by every evaluator.

    Subclasses must implement :meth:`evaluate` and return an
    :class:`app.schemas.EvaluationResult`. Lifecycle hooks are intentionally
    no-ops so evaluators can opt in without introducing SDK business logic.
    """

    def __init__(self, evaluator_name: str | None = None, version: str = "0.1.0") -> None:
        """Initialize common evaluator metadata.

        Args:
            evaluator_name: Optional explicit evaluator name. Defaults to the class name.
            version: Evaluator implementation version.
        """
        self._evaluator_name = evaluator_name or self.__class__.__name__
        self._version = version

    @property
    def evaluator_name(self) -> str:
        """Return the evaluator name."""
        return self._evaluator_name

    @property
    def version(self) -> str:
        """Return the evaluator version."""
        return self._version

    async def initialize(self, context: EvaluationContext) -> None:
        """Initialize evaluator resources before use."""
        _ = context

    async def shutdown(self, context: EvaluationContext) -> None:
        """Release evaluator resources after use."""
        _ = context

    def validate_input(self, conversation: Conversation, context: EvaluationContext) -> None:
        """Validate generic evaluator input.

        Args:
            conversation: Conversation to evaluate.
            context: Request context for this evaluation.

        Raises:
            InvalidConversationException: If the conversation contains no turns.
        """
        if conversation.total_turns == 0:
            raise InvalidConversationException("conversation must contain at least one turn")

    async def before_evaluate(self, conversation: Conversation, context: EvaluationContext) -> None:
        """Run before evaluation starts."""
        self.validate_input(conversation, context)

    async def after_evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
        result: EvaluationResult,
    ) -> None:
        """Run after evaluation completes."""
        _ = (conversation, context, result)

    @abstractmethod
    async def evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Evaluate a conversation and return a typed result."""
