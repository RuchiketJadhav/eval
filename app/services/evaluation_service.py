"""Application service for transcript evaluation."""

from app.config.settings import AppSettings
from app.evaluators.quality import QualityEvaluator
from app.schemas import QualityEvaluationReport
from app.sdk import EvaluatorLogger
from app.services.openai_client import OpenAIQualityClient


class TranscriptEvaluationService:
    """Coordinates web transcript evaluation using the Quality Evaluator."""

    def __init__(self, settings: AppSettings, logger: EvaluatorLogger | None = None) -> None:
        """Initialize the evaluation service."""
        self._settings = settings
        self._logger = logger or EvaluatorLogger("transcript_evaluation_service")

    async def evaluate(self, transcript: str) -> QualityEvaluationReport:
        """Evaluate a transcript and return a quality report."""
        cleaned_transcript = transcript.strip()
        if not cleaned_transcript:
            raise ValueError("Transcript is required.")
        client = OpenAIQualityClient(
            api_key=self._settings.openai_api_key,
            model=self._settings.openai_model,
            timeout_seconds=self._settings.request_timeout_seconds,
        )
        evaluator = QualityEvaluator(client)
        self._logger.info("quality_evaluation_started", transcript_length=len(cleaned_transcript))
        report = await evaluator.evaluate_transcript(cleaned_transcript)
        self._logger.info("quality_evaluation_completed", overall_score=report.overall_score)
        return report
