"""Health-check API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response returned by health-check endpoints."""

    model_config = ConfigDict(frozen=True)

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health information."""
    return HealthResponse(status="ok", service="evaluation-engine")
