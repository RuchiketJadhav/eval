"""Tests for MVP quality evaluation components."""

import asyncio

import pytest
from app.api.web import SAMPLE_TRANSCRIPT
from app.evaluators.quality import QUALITY_EVALUATION_PROMPT, QualityEvaluator
from app.schemas import QualityEvaluationReport
from app.sdk import EvaluatorConfigurationException
from app.services.openai_client import OpenAIQualityClient


class FakeQualityClient:
    """Fake OpenAI client for evaluator tests."""

    def __init__(self) -> None:
        """Initialize fake client state."""
        self.prompt = ""

    async def evaluate_transcript(self, prompt: str) -> QualityEvaluationReport:
        """Return a deterministic quality report."""
        self.prompt = prompt
        return QualityEvaluationReport(
            overall_score=92,
            intent_score=95,
            response_score=90,
            context_score=91,
            flow_score=93,
            completion_score=94,
            summary="The AI agent resolved the customer request effectively.",
            strengths=["Clear confirmation", "Goal completed"],
            weaknesses=["Could provide a reference number"],
            issues=[],
            recommendations=[],
        )


def test_quality_evaluator_uses_single_structured_prompt() -> None:
    """QualityEvaluator builds the enterprise QA prompt and returns typed reports."""
    client = FakeQualityClient()
    evaluator = QualityEvaluator(client)  # type: ignore[arg-type]

    report = asyncio.run(evaluator.evaluate_transcript(SAMPLE_TRANSCRIPT))

    assert report.overall_score == 92
    assert "enterprise AI voice quality assurance system" in client.prompt
    assert SAMPLE_TRANSCRIPT in client.prompt
    assert QUALITY_EVALUATION_PROMPT.count("{transcript}") == 1


def test_openai_client_requires_api_key() -> None:
    """OpenAI client refuses to run without an API key."""
    with pytest.raises(EvaluatorConfigurationException, match="OPENAI_API_KEY"):
        OpenAIQualityClient(api_key=None, model="gpt-4.1", timeout_seconds=45)
