"""Quality evaluator for AI voice conversations."""

from app.schemas import (
    Conversation,
    EvaluationResult,
    EvaluationStatus,
    QualityEvaluationReport,
)
from app.sdk import BaseEvaluator, EvaluationContext, EvaluationTimer
from app.services.openai_client import OpenAIQualityClient

QUALITY_EVALUATION_PROMPT = """You are an enterprise AI voice quality assurance system.

Evaluate the AI agent conversation transcript objectively across exactly five dimensions:
1. Intent Understanding — did the AI understand the customer intent?
2. Response Correctness — were answers correct and free from hallucination?
3. Context Retention — did the AI remember details and avoid contradictions?
4. Conversation Flow — was the dialogue natural, non-repetitive, and coherent?
5. Task Completion — did the customer accomplish their goal?

Rules:
- Use only evidence from the transcript.
- Do not assume facts not present in the transcript.
- Score each metric from 0 to 100.
- Support every issue with transcript evidence.
- Return only the structured JSON object requested by the schema.
- Be fair: do not over-penalize missing information when the transcript lacks enough context.

Transcript:
{transcript}
"""


class QualityEvaluator(BaseEvaluator):
    """Evaluator that produces a structured quality report with one LLM call."""

    def __init__(self, openai_client: OpenAIQualityClient) -> None:
        """Initialize the quality evaluator."""
        super().__init__(evaluator_name="quality", version="1.0.0")
        self._openai_client = openai_client

    async def evaluate_transcript(self, transcript: str) -> QualityEvaluationReport:
        """Evaluate a raw transcript and return a quality report."""
        prompt = QUALITY_EVALUATION_PROMPT.format(transcript=transcript.strip())
        return await self._openai_client.evaluate_transcript(prompt)

    async def evaluate(
        self,
        conversation: Conversation,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """Evaluate a typed conversation and return the SDK evaluation result."""
        await self.before_evaluate(conversation, context)
        transcript = "\n".join(f"{turn.speaker.value}: {turn.text}" for turn in conversation.turns)
        async with EvaluationTimer() as timer:
            report = await self.evaluate_transcript(transcript)
        result = EvaluationResult(
            evaluator_name=self.evaluator_name,
            status=EvaluationStatus.SUCCESS,
            score=report.overall_score,
            confidence=1.0,
            execution_time_ms=timer.elapsed_ms,
            metadata={"quality_report": report.model_dump(mode="json")},
        )
        await self.after_evaluate(conversation, context, result)
        return result
