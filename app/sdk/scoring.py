"""Evaluator-agnostic scoring utilities."""


def clamp_score(score: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp a score to an inclusive range.

    Args:
        score: Score to clamp.
        minimum: Inclusive lower bound.
        maximum: Inclusive upper bound.

    Returns:
        The score constrained to the provided range.

    Raises:
        ValueError: If minimum is greater than maximum.
    """
    if minimum > maximum:
        msg = "minimum cannot be greater than maximum"
        raise ValueError(msg)
    return min(max(score, minimum), maximum)


def normalize_score(
    value: float,
    source_minimum: float,
    source_maximum: float,
    target_minimum: float = 0.0,
    target_maximum: float = 100.0,
) -> float:
    """Normalize a value from one numeric range into another range."""
    if source_minimum == source_maximum:
        msg = "source range cannot be zero"
        raise ValueError(msg)
    if target_minimum > target_maximum:
        msg = "target_minimum cannot be greater than target_maximum"
        raise ValueError(msg)
    ratio = (value - source_minimum) / (source_maximum - source_minimum)
    normalized = target_minimum + ratio * (target_maximum - target_minimum)
    return clamp_score(normalized, target_minimum, target_maximum)


def weighted_average(values: list[tuple[float, float]]) -> float:
    """Calculate the weighted average for score and weight pairs.

    Args:
        values: Pairs in the form ``(score, weight)``.

    Returns:
        Weighted average score, or ``0.0`` when no values are provided.

    Raises:
        ValueError: If any weight is negative or total weight is zero.
    """
    if not values:
        return 0.0
    if any(weight < 0 for _, weight in values):
        msg = "weights cannot be negative"
        raise ValueError(msg)
    total_weight = sum(weight for _, weight in values)
    if total_weight == 0:
        msg = "total weight must be greater than zero"
        raise ValueError(msg)
    return sum(score * weight for score, weight in values) / total_weight


def confidence_average(confidences: list[float]) -> float:
    """Calculate the arithmetic mean for confidence scores.

    Args:
        confidences: Confidence scores, each between 0 and 1.

    Returns:
        Average confidence, or ``0.0`` when no confidences are provided.

    Raises:
        ValueError: If any confidence is outside the inclusive 0 to 1 range.
    """
    if not confidences:
        return 0.0
    if any(confidence < 0 or confidence > 1 for confidence in confidences):
        msg = "confidence values must be between 0 and 1"
        raise ValueError(msg)
    return sum(confidences) / len(confidences)
