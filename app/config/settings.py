"""Application settings."""

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

class AppSettings(BaseModel):
    """Runtime settings for the evaluation engine."""

    model_config = ConfigDict(frozen=True)

    app_name: str = "AI Voice Evaluation Platform"
    environment: str = "local"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"
    request_timeout_seconds: float = Field(default=45, gt=0)


def get_settings() -> AppSettings:
    """Return application settings loaded from environment variables."""
    return AppSettings(
        app_name=os.getenv("APP_NAME", "AI Voice Evaluation Platform"),
        environment=os.getenv("APP_ENV", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45")),
    )
