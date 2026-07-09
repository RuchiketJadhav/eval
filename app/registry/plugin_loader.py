"""Dynamic evaluator plugin module loading."""

import pkgutil
from importlib import import_module
from types import ModuleType

from app.registry.evaluator_registry import PluginLoadError
from app.sdk import EvaluatorLogger


def load_plugin_module(module_name: str, logger: EvaluatorLogger | None = None) -> ModuleType:
    """Import one plugin module by dotted module name.

    Args:
        module_name: Dotted Python module path to import.
        logger: Optional SDK logger used for load events.

    Returns:
        Imported module.

    Raises:
        PluginLoadError: If the module name is blank or import fails.
    """
    plugin_logger = logger or EvaluatorLogger("plugin_loader")
    if not module_name.strip():
        raise PluginLoadError("plugin module name must not be blank")
    try:
        module = import_module(module_name)
        plugin_logger.info("plugin_module_loaded", module_name=module_name)
        return module
    except Exception as exc:
        plugin_logger.error("plugin_module_load_failed", module_name=module_name, error=str(exc))
        raise PluginLoadError(f"failed to load plugin module '{module_name}'") from exc


def load_plugin_modules(
    package_name: str = "app.evaluators",
    logger: EvaluatorLogger | None = None,
) -> tuple[ModuleType, ...]:
    """Import every module in a plugin package.

    Args:
        package_name: Dotted Python package path to scan.
        logger: Optional SDK logger used for load events.

    Returns:
        Imported plugin modules.

    Raises:
        PluginLoadError: If the package cannot be imported or scanned.
    """
    plugin_logger = logger or EvaluatorLogger("plugin_loader")
    try:
        package = import_module(package_name)
    except Exception as exc:
        plugin_logger.error("plugin_package_load_failed", package_name=package_name, error=str(exc))
        raise PluginLoadError(f"failed to load plugin package '{package_name}'") from exc

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise PluginLoadError(f"plugin package '{package_name}' is not a package")

    modules: list[ModuleType] = []
    for module_info in pkgutil.walk_packages(package_path, prefix=f"{package_name}."):
        if module_info.ispkg:
            continue
        modules.append(load_plugin_module(module_info.name, logger=plugin_logger))
    plugin_logger.info(
        "plugin_modules_loaded",
        package_name=package_name,
        plugin_count=len(modules),
    )
    return tuple(modules)
