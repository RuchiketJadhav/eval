"""Thread-safe evaluator registry."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import cast

from app.sdk import BaseEvaluator, EvaluatorLogger


class RegistryError(Exception):
    """Base error for evaluator registry failures."""


class DuplicateEvaluatorError(RegistryError):
    """Raised when an evaluator name or class is already registered."""


class EvaluatorNotFoundError(RegistryError):
    """Raised when a requested evaluator is not registered."""


class PluginLoadError(RegistryError):
    """Raised when a plugin module cannot be loaded."""


class DiscoveryError(RegistryError):
    """Raised when plugin discovery fails."""


class RegistrationError(RegistryError):
    """Raised when evaluator registration input is invalid."""


EvaluatorProvider = BaseEvaluator | type[BaseEvaluator] | Callable[[], BaseEvaluator]


@dataclass(frozen=True)
class _RegistryEntry:
    """Internal registry entry for an evaluator provider."""

    name: str
    provider: EvaluatorProvider
    evaluator_class: type[BaseEvaluator] | None
    instance: BaseEvaluator | None = None


class EvaluatorRegistry:
    """Thread-safe registry for evaluator plugins.

    The registry only understands the :class:`app.sdk.BaseEvaluator` contract.
    Evaluators can be registered as instances, classes, or dependency-injected
    factories. Class and factory providers are lazily instantiated on lookup.
    """

    def __init__(self, logger: EvaluatorLogger | None = None) -> None:
        """Initialize an empty registry.

        Args:
            logger: Optional SDK logger used for registry events.
        """
        self._entries_by_name: dict[str, _RegistryEntry] = {}
        self._names_by_class: dict[type[BaseEvaluator], str] = {}
        self._lock = RLock()
        self._logger = logger or EvaluatorLogger("evaluator_registry")

    def register(
        self,
        provider: EvaluatorProvider,
        *,
        name: str | None = None,
        evaluator_class: type[BaseEvaluator] | None = None,
    ) -> None:
        """Register an evaluator provider.

        Args:
            provider: Evaluator instance, evaluator class, or zero-argument factory.
            name: Optional explicit evaluator name. Required for factory providers.
            evaluator_class: Optional evaluator class for factory providers.

        Raises:
            DuplicateEvaluatorError: If the name or known class is already registered.
            RegistrationError: If the provider is invalid.
        """
        entry = self._build_entry(provider, name=name, evaluator_class=evaluator_class)
        with self._lock:
            self._reject_duplicate_entry(entry)
            self._entries_by_name[entry.name] = entry
            if entry.evaluator_class is not None:
                self._names_by_class[entry.evaluator_class] = entry.name
        self._logger.info("evaluator_registered", evaluator_name=entry.name)

    def unregister(self, evaluator: str | type[BaseEvaluator]) -> None:
        """Unregister an evaluator by name or class.

        Raises:
            EvaluatorNotFoundError: If the evaluator is not registered.
        """
        with self._lock:
            name = self._resolve_name(evaluator)
            entry = self._entries_by_name.pop(name)
            if entry.evaluator_class is not None:
                self._names_by_class.pop(entry.evaluator_class, None)
        self._logger.info("evaluator_unregistered", evaluator_name=name)

    def get(self, name: str) -> BaseEvaluator:
        """Return an evaluator instance by name.

        Class and factory providers are instantiated lazily and cached after the
        first successful lookup.
        """
        with self._lock:
            entry = self._entries_by_name.get(name)
            if entry is None:
                self._logger.error("evaluator_not_found", evaluator_name=name)
                raise EvaluatorNotFoundError(f"evaluator '{name}' is not registered")
            evaluator = self._resolve_entry_instance(entry)
            return evaluator

    def get_by_class(self, evaluator_class: type[BaseEvaluator]) -> BaseEvaluator:
        """Return an evaluator instance by registered class."""
        with self._lock:
            name = self._resolve_name(evaluator_class)
        return self.get(name)

    def list(self) -> tuple[str, ...]:
        """List registered evaluator names in insertion order."""
        with self._lock:
            return tuple(self._entries_by_name.keys())

    def exists(self, evaluator: str | type[BaseEvaluator]) -> bool:
        """Return whether an evaluator name or class is registered."""
        with self._lock:
            if isinstance(evaluator, str):
                return evaluator in self._entries_by_name
            return evaluator in self._names_by_class

    def clear(self) -> None:
        """Clear all registered evaluators."""
        with self._lock:
            self._entries_by_name.clear()
            self._names_by_class.clear()
        self._logger.info("registry_cleared")

    def discover(self, package_name: str = "app.evaluators") -> tuple[type[BaseEvaluator], ...]:
        """Discover and register evaluator classes from a package."""
        from app.registry.discovery import discover_evaluator_classes

        try:
            evaluator_classes = discover_evaluator_classes(package_name)
            for evaluator_class in evaluator_classes:
                if not self.exists(evaluator_class):
                    self.register(evaluator_class)
            self._logger.info(
                "evaluator_discovery_completed",
                package_name=package_name,
                discovered_count=len(evaluator_classes),
            )
            return evaluator_classes
        except RegistryError:
            raise
        except Exception as exc:
            self._logger.error(
                "evaluator_discovery_failed", package_name=package_name, error=str(exc)
            )
            raise DiscoveryError(f"failed to discover evaluators in '{package_name}'") from exc

    def load_plugins(self, package_name: str = "app.evaluators") -> tuple[type[BaseEvaluator], ...]:
        """Load plugin modules and register discovered evaluator classes."""
        from app.registry.plugin_loader import load_plugin_modules

        try:
            modules = load_plugin_modules(package_name)
            self._logger.info(
                "evaluator_plugins_loaded",
                package_name=package_name,
                plugin_count=len(modules),
            )
            return self.discover(package_name)
        except RegistryError:
            raise
        except Exception as exc:
            self._logger.error(
                "evaluator_plugins_failed", package_name=package_name, error=str(exc)
            )
            raise PluginLoadError(
                f"failed to load evaluator plugins from '{package_name}'"
            ) from exc

    def _build_entry(
        self,
        provider: EvaluatorProvider,
        *,
        name: str | None,
        evaluator_class: type[BaseEvaluator] | None,
    ) -> _RegistryEntry:
        """Build a validated registry entry from a provider."""
        if isinstance(provider, BaseEvaluator):
            resolved_name = name or provider.evaluator_name
            return _RegistryEntry(
                name=self._validate_name(resolved_name),
                provider=provider,
                evaluator_class=type(provider),
                instance=provider,
            )
        if isinstance(provider, type):
            if not issubclass(provider, BaseEvaluator):
                raise RegistrationError("evaluator class must inherit BaseEvaluator")
            resolved_name = name or provider.__name__
            return _RegistryEntry(
                name=self._validate_name(resolved_name),
                provider=provider,
                evaluator_class=provider,
            )
        if callable(provider):
            if name is None:
                raise RegistrationError("factory providers require an evaluator name")
            if evaluator_class is not None and not issubclass(evaluator_class, BaseEvaluator):
                raise RegistrationError("evaluator_class must inherit BaseEvaluator")
            return _RegistryEntry(
                name=self._validate_name(name),
                provider=provider,
                evaluator_class=evaluator_class,
            )
        raise RegistrationError("provider must be an evaluator instance, class, or factory")

    def _reject_duplicate_entry(self, entry: _RegistryEntry) -> None:
        """Reject duplicate evaluator names and known classes."""
        if entry.name in self._entries_by_name:
            self._logger.warning("duplicate_evaluator_name", evaluator_name=entry.name)
            raise DuplicateEvaluatorError(f"evaluator name '{entry.name}' is already registered")
        if entry.evaluator_class is not None and entry.evaluator_class in self._names_by_class:
            existing_name = self._names_by_class[entry.evaluator_class]
            self._logger.warning(
                "duplicate_evaluator_class",
                evaluator_name=entry.name,
                existing_name=existing_name,
            )
            raise DuplicateEvaluatorError(
                f"evaluator class '{entry.evaluator_class.__name__}' is already registered"
            )

    def _resolve_entry_instance(self, entry: _RegistryEntry) -> BaseEvaluator:
        """Resolve a registry entry to an evaluator instance."""
        if entry.instance is not None:
            return entry.instance
        evaluator = self._instantiate_provider(entry.provider)
        if not isinstance(evaluator, BaseEvaluator):
            self._logger.error("invalid_evaluator_factory_result", evaluator_name=entry.name)
            raise RegistrationError(
                f"provider for evaluator '{entry.name}' did not return BaseEvaluator"
            )
        updated_entry = _RegistryEntry(
            name=entry.name,
            provider=entry.provider,
            evaluator_class=entry.evaluator_class or type(evaluator),
            instance=evaluator,
        )
        self._entries_by_name[entry.name] = updated_entry
        if updated_entry.evaluator_class is not None:
            self._names_by_class.setdefault(updated_entry.evaluator_class, entry.name)
        return evaluator

    def _instantiate_provider(self, provider: EvaluatorProvider) -> BaseEvaluator:
        """Instantiate a class or factory provider."""
        if isinstance(provider, BaseEvaluator):
            return provider
        if isinstance(provider, type):
            return cast(BaseEvaluator, provider())
        return provider()

    def _resolve_name(self, evaluator: str | type[BaseEvaluator]) -> str:
        """Resolve evaluator name from a name or class lookup."""
        if isinstance(evaluator, str):
            if evaluator not in self._entries_by_name:
                raise EvaluatorNotFoundError(f"evaluator '{evaluator}' is not registered")
            return evaluator
        name = self._names_by_class.get(evaluator)
        if name is None:
            raise EvaluatorNotFoundError(
                f"evaluator class '{evaluator.__name__}' is not registered"
            )
        return name

    def _validate_name(self, name: str) -> str:
        """Validate a registry name."""
        if not name.strip():
            raise RegistrationError("evaluator name must not be blank")
        return name


_DEFAULT_REGISTRY = EvaluatorRegistry()


def get_registry() -> EvaluatorRegistry:
    """Return the process-wide singleton evaluator registry."""
    return _DEFAULT_REGISTRY
