"""SDK-level exception types for evaluator execution."""


class EvaluationException(Exception):
    """Base exception for evaluator SDK failures."""


class InvalidConversationException(EvaluationException):
    """Raised when an evaluator receives an invalid conversation."""


class EvaluationTimeoutException(EvaluationException):
    """Raised when evaluator execution exceeds its allowed time budget."""


class EvaluatorConfigurationException(EvaluationException):
    """Raised when evaluator configuration is invalid."""
