"""Tests for the health-check API."""

import asyncio

from app.api.health import HealthResponse, health_check
from app.main import create_app


def test_create_app_configures_health_route() -> None:
    """The application factory registers the health-check route."""
    app = create_app()

    schema = app.openapi()

    assert "/health" in schema["paths"]


def test_health_check_returns_ok() -> None:
    """The health-check endpoint handler returns basic service status."""
    response = asyncio.run(health_check())

    assert isinstance(response, HealthResponse)
    assert response.model_dump() == {"status": "ok", "service": "evaluation-engine"}
