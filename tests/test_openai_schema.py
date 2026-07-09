"""Tests for OpenAI structured output schema compatibility."""

from typing import Any

from app.schemas import QualityEvaluationReport
from app.services.openai_client import build_strict_json_schema


def test_quality_report_schema_disallows_additional_properties_on_all_objects() -> None:
    """Every object in the Responses API schema sets additionalProperties=false."""
    schema = build_strict_json_schema(QualityEvaluationReport)

    object_schemas = _collect_object_schemas(schema)

    assert object_schemas
    assert all(fragment.get("additionalProperties") is False for fragment in object_schemas)


def _collect_object_schemas(schema_fragment: Any) -> list[dict[str, Any]]:
    """Collect all object schema fragments recursively."""
    object_schemas: list[dict[str, Any]] = []
    if isinstance(schema_fragment, dict):
        if schema_fragment.get("type") == "object" or "properties" in schema_fragment:
            object_schemas.append(schema_fragment)
        for value in schema_fragment.values():
            object_schemas.extend(_collect_object_schemas(value))
    elif isinstance(schema_fragment, list):
        for item in schema_fragment:
            object_schemas.extend(_collect_object_schemas(item))
    return object_schemas
