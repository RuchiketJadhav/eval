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
    """Return application settings loaded from environment variables and .env."""
    env_values = _read_dotenv(Path(".env"))
    return AppSettings(
        app_name=_get_setting("APP_NAME", env_values, "AI Voice Evaluation Platform"),
        environment=_get_setting("APP_ENV", env_values, "local"),
        log_level=_get_setting("LOG_LEVEL", env_values, "INFO"),
        openai_api_key=_get_optional_setting("OPENAI_API_KEY", env_values),
        openai_model=_get_setting("OPENAI_MODEL", env_values, "gpt-5"),
        request_timeout_seconds=float(_get_setting("REQUEST_TIMEOUT_SECONDS", env_values, "45")),
    )


def _get_setting(name: str, env_values: dict[str, str], default: str) -> str:
    """Return a setting from environment variables, .env, or a default."""
    return os.getenv(name) or env_values.get(name, default)


def _get_optional_setting(name: str, env_values: dict[str, str]) -> str | None:
    """Return an optional setting from environment variables or .env."""
    return os.getenv(name) or env_values.get(name)


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE pairs from a local .env file."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values
