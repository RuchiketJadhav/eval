"""Evaluator logging wrapper."""

from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger


class EvaluatorLogger:
    """Small wrapper around structlog for evaluator-facing logging.

    Attributes:
        logger_name: Name bound to the underlying structlog logger.
    """

    def __init__(self, logger_name: str = "evaluator") -> None:
        """Initialize the evaluator logger.

        Args:
            logger_name: Logger name used by structlog.
        """
        self.logger_name = logger_name
        self._logger: FilteringBoundLogger = structlog.get_logger(logger_name)

    def bind(self, **values: Any) -> "EvaluatorLogger":
        """Return a new logger with additional bound context."""
        logger = EvaluatorLogger(self.logger_name)
        logger._logger = self._logger.bind(**values)
        return logger

    def debug(self, event: str, **values: Any) -> None:
        """Log a debug event."""
        self._logger.debug(event, **values)

    def info(self, event: str, **values: Any) -> None:
        """Log an info event."""
        self._logger.info(event, **values)

    def warning(self, event: str, **values: Any) -> None:
        """Log a warning event."""
        self._logger.warning(event, **values)

    def error(self, event: str, **values: Any) -> None:
        """Log an error event."""
        self._logger.error(event, **values)
