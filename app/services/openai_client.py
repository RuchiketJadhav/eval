"""OpenAI Responses API client wrapper."""

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from app.schemas import QualityEvaluationReport
from app.sdk import EvaluationException, EvaluatorConfigurationException


class OpenAIQualityClient:
    """Client that evaluates transcripts with one OpenAI Responses API call."""

    def __init__(self, api_key: str | None, model: str, timeout_seconds: float) -> None:
        """Initialize the OpenAI quality client."""
        if not api_key:
            raise EvaluatorConfigurationException(
                "OPENAI_API_KEY is required to run AI quality evaluations"
            )
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise EvaluatorConfigurationException(
                "The openai package is required to run AI quality evaluations"
            ) from exc
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model = model

    async def evaluate_transcript(self, prompt: str) -> QualityEvaluationReport:
        """Evaluate a transcript and parse the structured quality report."""
        try:
            response = await self._client.responses.create(
                model=self._model,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "quality_evaluation_report",
                        "strict": True,
                        "schema": build_strict_json_schema(QualityEvaluationReport),
                    }
                },
            )
            raw_json = getattr(response, "output_text", None)
            if not isinstance(raw_json, str) or not raw_json.strip():
                raw_json = self._extract_output_text(response)
            return QualityEvaluationReport.model_validate_json(raw_json)
        except ValidationError as exc:
            raise EvaluationException(
                "OpenAI returned an invalid quality evaluation payload"
            ) from exc
        except Exception as exc:
            raise EvaluationException("OpenAI quality evaluation request failed") from exc

    def _extract_output_text(self, response: Any) -> str:
        """Extract text from a Responses API response when output_text is unavailable."""
        payload = response.model_dump() if hasattr(response, "model_dump") else response
        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if not chunks:
            raise EvaluationException("OpenAI response did not include output text")
        text = "".join(chunks)
        json.loads(text)
        return text


def build_strict_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Build an OpenAI-compatible strict JSON schema for a Pydantic model."""
    schema = model.model_json_schema()
    _require_no_additional_properties(schema)
    return schema


def _require_no_additional_properties(schema_fragment: Any) -> None:
    """Recursively set additionalProperties=false on every object schema."""
    if isinstance(schema_fragment, dict):
        if schema_fragment.get("type") == "object" or "properties" in schema_fragment:
            schema_fragment["additionalProperties"] = False
        for value in schema_fragment.values():
            _require_no_additional_properties(value)
    elif isinstance(schema_fragment, list):
        for item in schema_fragment:
            _require_no_additional_properties(item)
