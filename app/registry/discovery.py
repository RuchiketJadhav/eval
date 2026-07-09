"""Evaluator plugin discovery utilities."""

import inspect
from importlib import import_module

from app.registry.evaluator_registry import DiscoveryError
from app.registry.plugin_loader import load_plugin_modules
from app.sdk import BaseEvaluator, EvaluatorLogger


def discover_evaluator_classes(
    package_name: str = "app.evaluators",
    logger: EvaluatorLogger | None = None,
) -> tuple[type[BaseEvaluator], ...]:
    """Discover concrete ``BaseEvaluator`` subclasses in a package.

    Args:
        package_name: Dotted Python package path to scan.
        logger: Optional SDK logger used for discovery events.

    Returns:
        Discovered concrete evaluator classes.

    Raises:
        DiscoveryError: If the package or plugin modules cannot be inspected.
    """
    discovery_logger = logger or EvaluatorLogger("evaluator_discovery")
    try:
        package = import_module(package_name)
        modules = [package, *load_plugin_modules(package_name, logger=discovery_logger)]
        evaluator_classes: list[type[BaseEvaluator]] = []
        seen: set[type[BaseEvaluator]] = set()
        for module in modules:
            for _, candidate in inspect.getmembers(module, inspect.isclass):
                if _is_concrete_evaluator(candidate) and candidate not in seen:
                    evaluator_classes.append(candidate)
                    seen.add(candidate)
        discovery_logger.info(
            "evaluator_classes_discovered",
            package_name=package_name,
            discovered_count=len(evaluator_classes),
        )
        return tuple(evaluator_classes)
    except DiscoveryError:
        raise
    except Exception as exc:
        discovery_logger.error(
            "evaluator_discovery_failed", package_name=package_name, error=str(exc)
        )
        raise DiscoveryError(f"failed to discover evaluator classes in '{package_name}'") from exc


def _is_concrete_evaluator(candidate: type[object]) -> bool:
    """Return whether a class is a concrete BaseEvaluator implementation."""
    return (
        inspect.isclass(candidate)
        and issubclass(candidate, BaseEvaluator)
        and candidate is not BaseEvaluator
        and not inspect.isabstract(candidate)
    )
