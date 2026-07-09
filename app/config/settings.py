"""Application settings."""

from pydantic import BaseModel, ConfigDict


class AppSettings(BaseModel):
    """Runtime settings for the evaluation engine."""

    model_config = ConfigDict(frozen=True)

    app_name: str = "AI Voice Evaluation Platform"
    environment: str = "local"
    log_level: str = "INFO"


def get_settings() -> AppSettings:
    """Return application settings."""
    return AppSettings()
