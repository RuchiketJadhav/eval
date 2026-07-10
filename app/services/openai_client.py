"""OpenAI Responses API client wrapper."""

from pydantic import ValidationError

from app.schemas import QualityEvaluationReport
from app.sdk import EvaluationException, EvaluatorConfigurationException


def build_strict_json_schema(model_type: type[QualityEvaluationReport]) -> dict[str, object]:
    """Build a strict JSON schema for OpenAI structured output tests."""
    schema = model_type.model_json_schema()
    _disallow_additional_properties(schema)
    return schema


def _disallow_additional_properties(schema_fragment: object) -> None:
    """Recursively mark object schemas as closed to extra properties."""
    if isinstance(schema_fragment, dict):
        if schema_fragment.get("type") == "object" or "properties" in schema_fragment:
            schema_fragment["additionalProperties"] = False
        for value in schema_fragment.values():
            _disallow_additional_properties(value)
    elif isinstance(schema_fragment, list):
        for item in schema_fragment:
            _disallow_additional_properties(item)


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
            response = await self._client.responses.parse(
                model=self._model,
                input=prompt,
                text_format=QualityEvaluationReport,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise EvaluationException("OpenAI response did not include parsed output")
            if not isinstance(parsed, QualityEvaluationReport):
                raise EvaluationException(
                    f"OpenAI returned unexpected parsed type: {type(parsed).__name__}"
                )
            return parsed
        except ValidationError as exc:
            raise EvaluationException(
                "OpenAI returned an invalid quality evaluation payload"
            ) from exc
        except Exception as exc:
            raise EvaluationException(
                f"OpenAI quality evaluation request failed: {type(exc).__name__}: {exc}"
            ) from exc
