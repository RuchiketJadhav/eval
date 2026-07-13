"""Quality evaluator for AI voice conversations."""

from app.schemas import (
    Conversation,
    EvaluationResult,
    EvaluationStatus,
    QualityEvaluationReport,
)
from app.sdk import BaseEvaluator, EvaluationContext, EvaluationTimer
from app.services.openai_client import OpenAIQualityClient

QUALITY_EVALUATION_PROMPT = """You are a Senior AI Conversation QA Analyst.
You investigate AI voice conversations within an enterprise AI voice quality assurance system.

Your job is not to start by scoring. Produce an evidence-led investigation using the
structured JSON schema. Follow this exact analysis order:

1. Extract factual evidence from the transcript.
2. Identify failure modes supported by that evidence.
3. Explain probable root causes and clearly distinguish inference from observation.
4. Analyze funnel progression through the standard stages.
5. Estimate business impact.
6. Produce actionable recommendations prioritized by business impact.
7. Finally produce numerical quality scores.

Standard funnel stages:
- Greeting
- Intent Recognition
- Information Gathering
- Resolution
- Confirmation
- Closure

Quality score rules:
- quality_scores.overall, intent, response, context, flow, and completion MUST each use a 0 to 100 scale.
- 0 means complete failure and 100 means excellent performance.
- Do NOT use a 0 to 1 scale for quality_scores.
- Use the full 0 to 100 range and assign scores that reflect the severity of transcript evidence.
- Confidence fields are different: confidence MUST remain on a 0 to 1 scale.

Rules:
- Use transcript evidence only.
- Never invent facts, customer goals, system capabilities, tool calls, policies, or outcomes.
- Evidence entries must be observable facts, not opinions or interpretations.
- Every failure mode must reference one or more evidence_ids.
- If the transcript does not support a conclusion, say confidence is low or mark the risk
  as unknown.
- Distinguish observations (what happened) from inferences (why it likely happened).
- Prefer concise, specific root-cause reasoning over generic criticism.
- Prioritize recommendations by expected business impact and customer harm reduction.
- Return only the structured JSON object requested by the schema.

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
