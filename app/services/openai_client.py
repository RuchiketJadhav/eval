"""OpenAI Responses API client wrapper."""

import json
from typing import Any

from pydantic import ValidationError

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
            raise EvaluationException(
                f"OpenAI quality evaluation request failed: {type(exc).__name__}: {exc}"
            ) from exc

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
