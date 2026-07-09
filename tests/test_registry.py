"""Tests for the evaluator registry."""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from app.registry import (
    DiscoveryError,
    DuplicateEvaluatorError,
    EvaluatorNotFoundError,
    EvaluatorRegistry,
    PluginLoadError,
    RegistrationError,
    discover_evaluator_classes,
    load_plugin_module,
    load_plugin_modules,
)
from app.schemas import Conversation, EvaluationResult, EvaluationStatus
from app.sdk import BaseEvaluator, EvaluationContext


class RegistryTestEvaluator(BaseEvaluator):
    """Concrete evaluator used by registry tests."""

    async def evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Return a minimal successful evaluation result."""
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            status=EvaluationStatus.SUCCESS,
            score=100,
            confidence=1,
            execution_time_ms=1,
        )


class AlternateRegistryTestEvaluator(BaseEvaluator):
    """Second concrete evaluator used by registry tests."""

    async def evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Return a minimal successful evaluation result."""
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            status=EvaluationStatus.SUCCESS,
            score=90,
            confidence=0.9,
            execution_time_ms=1,
        )


def test_register_and_get_evaluator_instance() -> None:
    """Registry stores and retrieves evaluator instances by name."""
    registry = EvaluatorRegistry()
    evaluator = RegistryTestEvaluator(evaluator_name="test")

    registry.register(evaluator)

    assert registry.exists("test")
    assert registry.get("test") is evaluator
    assert registry.list() == ("test",)


def test_register_evaluator_class_is_lazy() -> None:
    """Registry lazily instantiates class providers on lookup."""
    registry = EvaluatorRegistry()

    registry.register(RegistryTestEvaluator)

    evaluator = registry.get("RegistryTestEvaluator")
    assert isinstance(evaluator, RegistryTestEvaluator)
    assert registry.get("RegistryTestEvaluator") is evaluator


def test_register_factory_supports_dependency_injection() -> None:
    """Registry accepts factories for dependency-injected evaluators."""
    registry = EvaluatorRegistry()

    def factory() -> BaseEvaluator:
        return RegistryTestEvaluator(evaluator_name="factory")

    registry.register(factory, name="factory", evaluator_class=RegistryTestEvaluator)

    evaluator = registry.get("factory")
    assert isinstance(evaluator, RegistryTestEvaluator)
    assert evaluator.evaluator_name == "factory"
    assert registry.get_by_class(RegistryTestEvaluator) is evaluator


def test_duplicate_registration_by_name_and_class_is_rejected() -> None:
    """Registry rejects duplicate evaluator names and duplicate evaluator classes."""
    registry = EvaluatorRegistry()
    registry.register(RegistryTestEvaluator, name="first")

    with pytest.raises(DuplicateEvaluatorError, match="name 'first'"):
        registry.register(AlternateRegistryTestEvaluator, name="first")

    with pytest.raises(DuplicateEvaluatorError, match="class 'RegistryTestEvaluator'"):
        registry.register(RegistryTestEvaluator, name="second")


def test_invalid_registration_inputs_are_rejected() -> None:
    """Registry validates provider types, blank names, and factory metadata."""
    registry = EvaluatorRegistry()

    with pytest.raises(RegistrationError, match="must inherit BaseEvaluator"):
        registry.register(object)  # type: ignore[arg-type]

    with pytest.raises(RegistrationError, match="factory providers require"):
        registry.register(lambda: RegistryTestEvaluator())

    with pytest.raises(RegistrationError, match="must not be blank"):
        registry.register(RegistryTestEvaluator, name=" ")

    def invalid_factory() -> Any:
        return object()

    registry.register(invalid_factory, name="invalid")
    with pytest.raises(RegistrationError, match="did not return BaseEvaluator"):
        registry.get("invalid")


def test_unregister_by_name_and_class() -> None:
    """Registry unregisters evaluators by either name or class."""
    registry = EvaluatorRegistry()
    registry.register(RegistryTestEvaluator, name="test")
    registry.unregister("test")

    assert not registry.exists("test")
    with pytest.raises(EvaluatorNotFoundError):
        registry.get("test")

    registry.register(RegistryTestEvaluator)
    registry.unregister(RegistryTestEvaluator)
    assert not registry.exists(RegistryTestEvaluator)


def test_lookup_by_class_and_missing_lookup_errors() -> None:
    """Registry retrieves by class and raises clear missing-evaluator errors."""
    registry = EvaluatorRegistry()
    registry.register(RegistryTestEvaluator)

    assert isinstance(registry.get_by_class(RegistryTestEvaluator), RegistryTestEvaluator)

    with pytest.raises(EvaluatorNotFoundError, match="missing"):
        registry.get("missing")

    with pytest.raises(EvaluatorNotFoundError, match="AlternateRegistryTestEvaluator"):
        registry.get_by_class(AlternateRegistryTestEvaluator)


def test_clear_registry() -> None:
    """Registry clear removes all names and classes."""
    registry = EvaluatorRegistry()
    registry.register(RegistryTestEvaluator)
    registry.register(AlternateRegistryTestEvaluator)

    registry.clear()

    assert registry.list() == ()
    assert not registry.exists(RegistryTestEvaluator)


def test_thread_safe_registration_and_reads() -> None:
    """Registry mutation and reads are safe under concurrent access."""
    registry = EvaluatorRegistry()

    def register(index: int) -> None:
        registry.register(
            lambda: RegistryTestEvaluator(evaluator_name=f"evaluator-{index}"),
            name=f"evaluator-{index}",
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(register, range(20)))

    def read(name: str) -> bool:
        return registry.exists(name) and registry.get(name).evaluator_name == name

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(read, registry.list()))

    assert all(results)
    assert len(registry.list()) == 20


def test_load_plugin_module_and_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Plugin loader imports individual modules and whole plugin packages."""
    package_name = _write_plugin_package(tmp_path, "loader_plugins")
    monkeypatch.syspath_prepend(str(tmp_path))

    module = load_plugin_module(f"{package_name}.sample")
    modules = load_plugin_modules(package_name)

    assert module.__name__ == f"{package_name}.sample"
    assert [loaded_module.__name__ for loaded_module in modules] == [f"{package_name}.sample"]


def test_plugin_load_errors() -> None:
    """Plugin loading raises typed errors for invalid modules and packages."""
    with pytest.raises(PluginLoadError, match="must not be blank"):
        load_plugin_module(" ")

    with pytest.raises(PluginLoadError, match="failed to load plugin module"):
        load_plugin_module("missing.module")

    with pytest.raises(PluginLoadError, match="not a package"):
        load_plugin_modules("app.sdk.scoring")


def test_discover_evaluator_classes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Discovery finds concrete BaseEvaluator subclasses in plugin packages."""
    package_name = _write_plugin_package(tmp_path, "discovery_plugins")
    monkeypatch.syspath_prepend(str(tmp_path))

    evaluator_classes = discover_evaluator_classes(package_name)

    assert [evaluator_class.__name__ for evaluator_class in evaluator_classes] == [
        "DiscoveredEvaluator"
    ]


def test_registry_discover_and_load_plugins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Registry discovers plugins and registers discovered evaluator classes."""
    package_name = _write_plugin_package(tmp_path, "registry_plugins")
    monkeypatch.syspath_prepend(str(tmp_path))
    registry = EvaluatorRegistry()

    discovered = registry.discover(package_name)
    loaded = registry.load_plugins(package_name)

    assert [evaluator_class.__name__ for evaluator_class in discovered] == ["DiscoveredEvaluator"]
    assert [evaluator_class.__name__ for evaluator_class in loaded] == ["DiscoveredEvaluator"]
    assert registry.exists("DiscoveredEvaluator")
    assert registry.get("DiscoveredEvaluator").evaluator_name == "DiscoveredEvaluator"


def test_discovery_error_for_missing_package() -> None:
    """Discovery raises a typed error when the package cannot be imported."""
    with pytest.raises(DiscoveryError, match="failed to discover"):
        discover_evaluator_classes("missing_plugins")


def _write_plugin_package(tmp_path: Path, package_name: str) -> str:
    """Write a temporary plugin package containing one concrete evaluator."""
    package_dir = tmp_path / package_name
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "sample.py").write_text(
        "from app.schemas import Conversation, EvaluationResult, EvaluationStatus\n"
        "from app.sdk import BaseEvaluator, EvaluationContext\n\n"
        "class DiscoveredEvaluator(BaseEvaluator):\n"
        "    async def evaluate(\n"
        "        self, conversation: Conversation, context: EvaluationContext\n"
        "    ) -> EvaluationResult:\n"
        "        return EvaluationResult(\n"
        "            evaluator_name=self.evaluator_name,\n"
        "            status=EvaluationStatus.SUCCESS,\n"
        "            score=100,\n"
        "            confidence=1,\n"
        "            execution_time_ms=1,\n"
        "        )\n",
        encoding="utf-8",
    )
    sys.modules.pop(package_name, None)
    sys.modules.pop(f"{package_name}.sample", None)
    return package_name
