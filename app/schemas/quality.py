"""Quality evaluation report schemas for the MVP web application."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QualityIssueSeverity(StrEnum):
    """Severity levels returned for quality failures."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationPriority(StrEnum):
    """Priority levels returned for quality recommendations."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FailureModeCategory(StrEnum):
    """Failure categories for AI conversation quality investigations."""

    INTENT_MISCLASSIFICATION = "INTENT_MISCLASSIFICATION"
    CONTEXT_LOSS = "CONTEXT_LOSS"
    HALLUCINATION = "HALLUCINATION"
    WORKFLOW_FAILURE = "WORKFLOW_FAILURE"
    TOOL_FAILURE = "TOOL_FAILURE"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    COMMUNICATION_BREAKDOWN = "COMMUNICATION_BREAKDOWN"
    NO_TASK_COMPLETION = "NO_TASK_COMPLETION"


class ExecutiveSummary(BaseModel):
    """Executive summary of the conversation QA investigation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    call_status: str
    primary_failure: str
    customer_outcome: str
    business_severity: QualityIssueSeverity
    confidence: float = Field(ge=0, le=1)
    summary: str


class QualityEvidence(BaseModel):
    """Observable transcript fact used by the QA investigation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    speaker: str
    observation: str
    transcript_quote: str
    confidence: float = Field(ge=0, le=1)


class FailureMode(BaseModel):
    """Conversation failure supported by one or more evidence records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: FailureModeCategory
    severity: QualityIssueSeverity
    description: str
    evidence_ids: list[str]


class RootCause(BaseModel):
    """Probable cause analysis for an identified failure category."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_category: FailureModeCategory
    probable_cause: str
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    suggested_owner: str


class FunnelAnalysis(BaseModel):
    """Conversation funnel progression and drop-off analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stages_completed: list[str]
    dropoff_stage: str
    dropoff_reason: str
    task_completed: bool


class BusinessImpact(BaseModel):
    """Estimated business impact of the observed conversation outcome."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    customer_experience: str
    escalation_risk: str
    revenue_risk: str
    compliance_risk: str


class QualityRecommendation(BaseModel):
    """Actionable recommendation prioritized by business impact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    priority: RecommendationPriority
    recommendation: str
    rationale: str
    expected_impact: str


class QualityScores(BaseModel):
    """Numerical quality scores from the final step of the QA investigation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    overall: float = Field(ge=0, le=100)
    intent: float = Field(ge=0, le=100)
    response: float = Field(ge=0, le=100)
    context: float = Field(ge=0, le=100)
    flow: float = Field(ge=0, le=100)
    completion: float = Field(ge=0, le=100)


class QualityIssue(BaseModel):
    """Backward-compatible issue model for older integrations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    severity: QualityIssueSeverity
    title: str
    description: str
    evidence: str


class QualityEvaluationReport(BaseModel):
    """Structured investigation returned by the Quality Evaluator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    executive_summary: ExecutiveSummary
    evidence: list[QualityEvidence]
    failure_modes: list[FailureMode]
    root_causes: list[RootCause]
    funnel_analysis: FunnelAnalysis
    business_impact: BusinessImpact
    recommendations: list[QualityRecommendation]
    quality_scores: QualityScores

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy_payload(cls, data: Any) -> Any:
        """Accept the MVP score-first payload and convert it to the investigation shape."""
        if not isinstance(data, dict) or "quality_scores" in data:
            return data
        legacy_score_fields = {
            "overall_score",
            "intent_score",
            "response_score",
            "context_score",
            "flow_score",
            "completion_score",
        }
        if not legacy_score_fields.issubset(data):
            return data
        summary = str(data.get("summary", "Legacy quality evaluation report."))
        issues = data.get("issues", [])
        recommendations = data.get("recommendations", [])
        converted_evidence = [
            {
                "id": f"E{i + 1}",
                "speaker": "unknown",
                "observation": str(issue.get("description", issue.get("title", "Legacy issue")))
                if isinstance(issue, dict)
                else "Legacy issue",
                "transcript_quote": str(issue.get("evidence", "Not provided"))
                if isinstance(issue, dict)
                else "Not provided",
                "confidence": 0.5,
            }
            for i, issue in enumerate(issues)
        ]
        return {
            "executive_summary": {
                "call_status": "Evaluated",
                "primary_failure": "None identified" if not issues else "Legacy issue identified",
                "customer_outcome": summary,
                "business_severity": "LOW" if not issues else "MEDIUM",
                "confidence": 0.5,
                "summary": summary,
            },
            "evidence": converted_evidence,
            "failure_modes": [],
            "root_causes": [],
            "funnel_analysis": {
                "stages_completed": [],
                "dropoff_stage": "Unknown",
                "dropoff_reason": "Not provided in legacy report",
                "task_completed": data["completion_score"] >= 70,
            },
            "business_impact": {
                "customer_experience": summary,
                "escalation_risk": "Unknown",
                "revenue_risk": "Unknown",
                "compliance_risk": "Unknown",
            },
            "recommendations": [
                {
                    "priority": rec.get("priority", "LOW") if isinstance(rec, dict) else "LOW",
                    "recommendation": (
                        rec.get("title", rec.get("description", "Legacy recommendation"))
                        if isinstance(rec, dict)
                        else "Legacy recommendation"
                    ),
                    "rationale": rec.get("description", "Provided by legacy report")
                    if isinstance(rec, dict)
                    else "Provided by legacy report",
                    "expected_impact": "Improve conversation quality",
                }
                for rec in recommendations
            ],
            "quality_scores": {
                "overall": data["overall_score"],
                "intent": data["intent_score"],
                "response": data["response_score"],
                "context": data["context_score"],
                "flow": data["flow_score"],
                "completion": data["completion_score"],
            },
        }

    @field_validator("evidence")
    @classmethod
    def _evidence_ids_must_be_unique(cls, value: list[QualityEvidence]) -> list[QualityEvidence]:
        """Validate that evidence identifiers are unique."""
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence ids must be unique")
        return value

    @property
    def overall_score(self) -> float:
        """Backward-compatible alias for the overall quality score."""
        return self.quality_scores.overall

    @property
    def intent_score(self) -> float:
        """Backward-compatible alias for the intent quality score."""
        return self.quality_scores.intent

    @property
    def response_score(self) -> float:
        """Backward-compatible alias for the response quality score."""
        return self.quality_scores.response

    @property
    def context_score(self) -> float:
        """Backward-compatible alias for the context quality score."""
        return self.quality_scores.context

    @property
    def flow_score(self) -> float:
        """Backward-compatible alias for the flow quality score."""
        return self.quality_scores.flow

    @property
    def completion_score(self) -> float:
        """Backward-compatible alias for the completion quality score."""
        return self.quality_scores.completion

    @property
    def summary(self) -> str:
        """Backward-compatible alias for the executive summary text."""
        return self.executive_summary.summary
