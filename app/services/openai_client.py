"""OpenAI Responses API client wrapper."""

import json
from typing import Any

from pydantic import ValidationError

from app.schemas import QualityEvaluationReport
from app.sdk import EvaluationException, EvaluatorConfigurationException

QUALITY_EVALUATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
        "intent_score": {"type": "number", "minimum": 0, "maximum": 100},
        "response_score": {"type": "number", "minimum": 0, "maximum": 100},
        "context_score": {"type": "number", "minimum": 0, "maximum": 100},
        "flow_score": {"type": "number", "minimum": 0, "maximum": 100},
        "completion_score": {"type": "number", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "issues": {"type": "array", "items": {"$ref": "#/$defs/issue"}},
        "recommendations": {
            "type": "array",
            "items": {"$ref": "#/$defs/recommendation"},
        },
    },
    "required": [
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
    ],
    "$defs": {
        "issue": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
                "evidence": {"type": "string"},
            },
            "required": ["severity", "title", "description", "evidence"],
        },
        "recommendation": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["priority", "title", "description"],
        },
    },
}


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
                        "schema": QUALITY_EVALUATION_JSON_SCHEMA,
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
