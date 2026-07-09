"""Tests for OpenAI structured output schema compatibility."""

from typing import Any

from app.services.openai_client import QUALITY_EVALUATION_JSON_SCHEMA


def test_quality_report_schema_disallows_additional_properties_on_all_objects() -> None:
    """Every object in the Responses API schema sets additionalProperties=false."""
    object_schemas = _collect_object_schemas(QUALITY_EVALUATION_JSON_SCHEMA)

    assert object_schemas
    assert all(fragment.get("additionalProperties") is False for fragment in object_schemas)


def test_quality_report_schema_uses_expected_hand_written_shape() -> None:
    """The Responses API schema exposes the exact quality report fields."""
    assert set(QUALITY_EVALUATION_JSON_SCHEMA["properties"]) == {
        "overall_score",
        "intent_score",
        "response_score",
        "context_score",
        "flow_score",
        "completion_score",
        "summary",
        "strengths",
        "weaknesses",
        "issues",
        "recommendations",
    }
    assert QUALITY_EVALUATION_JSON_SCHEMA["properties"]["issues"]["items"] == {
        "$ref": "#/$defs/issue"
    }
    assert QUALITY_EVALUATION_JSON_SCHEMA["properties"]["recommendations"]["items"] == {
        "$ref": "#/$defs/recommendation"
    }


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
