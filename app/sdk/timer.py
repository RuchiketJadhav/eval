"""Async evaluator timing utility."""

from time import perf_counter
from types import TracebackType


class EvaluationTimer:
    """Async context manager that measures elapsed milliseconds.

    Example:
        async with EvaluationTimer() as timer:
            ...
        elapsed = timer.elapsed_ms
    """

    def __init__(self) -> None:
        """Initialize an inactive timer."""
        self._started_at: float | None = None
        self._ended_at: float | None = None

    async def __aenter__(self) -> "EvaluationTimer":
        """Start the timer and return it."""
        self._started_at = perf_counter()
        self._ended_at = None
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the timer when leaving the async context."""
        self._ended_at = perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Return elapsed time in milliseconds."""
        if self._started_at is None:
            return 0.0
        ended_at = self._ended_at if self._ended_at is not None else perf_counter()
        return (ended_at - self._started_at) * 1000
