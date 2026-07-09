"""Web routes for the evaluation product experience."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config.settings import get_settings
from app.sdk import EvaluationException, EvaluatorConfigurationException

router = APIRouter()

SAMPLE_TRANSCRIPT = """Customer: Hi, I need to change the delivery address for my order.
AI Agent: I can help with that. Can you provide your order number?
Customer: It is A12345.
AI Agent: Thanks. I found order A12345. What is the new delivery address?
Customer: 500 Market Street, San Francisco, California.
AI Agent: I updated the delivery address to 500 Market Street, San Francisco, California.
AI Agent: Your delivery date remains Friday.
Customer: Great, can you confirm there is no extra fee?
AI Agent: Correct, there is no extra fee for this address update.
Customer: Perfect, thank you.
AI Agent: You are welcome. Is there anything else I can help you with today?"""


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the transcript evaluation landing page."""
    return _template_response(
        request,
        "index.html",
        {"sample_transcript": SAMPLE_TRANSCRIPT},
    )


@router.post("/evaluate", response_class=HTMLResponse)
async def evaluate(request: Request) -> HTMLResponse:
    """Evaluate a transcript and render the report page."""
    form = await request.form()
    transcript = str(form.get("transcript", ""))
    if not transcript.strip():
        return _template_response(
            request,
            "index.html",
            {
                "sample_transcript": SAMPLE_TRANSCRIPT,
                "error": "Please paste a transcript before evaluating.",
            },
            status_code=400,
        )

    from app.services.evaluation_service import TranscriptEvaluationService

    service = TranscriptEvaluationService(get_settings())
    try:
        report = await service.evaluate(transcript)
    except EvaluatorConfigurationException as exc:
        return _render_error(request, transcript, str(exc), 503)
    except EvaluationException as exc:
        return _render_error(request, transcript, str(exc), 502)

    return _template_response(
        request,
        "report.html",
        {
            "report": report,
            "report_json": report.model_dump_json(indent=2),
            "transcript": transcript,
        },
    )


def _render_error(request: Request, transcript: str, error: str, status_code: int) -> HTMLResponse:
    """Render the landing page with an evaluation error."""
    return _template_response(
        request,
        "index.html",
        {
            "sample_transcript": SAMPLE_TRANSCRIPT,
            "transcript": transcript,
            "error": error,
        },
        status_code=status_code,
    )


def _template_response(
    request: Request,
    template_name: str,
    context: dict[str, Any],
    status_code: int = 200,
) -> HTMLResponse:
    """Render a template response with a lazy Jinja2 import."""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        request,
        template_name,
        context,
        status_code=status_code,
    )
