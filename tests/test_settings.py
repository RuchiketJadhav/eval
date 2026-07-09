"""Tests for environment-backed application settings."""

from pathlib import Path

import pytest
from app.config import settings as settings_module


def test_settings_load_openai_api_key_from_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Settings load OPENAI_API_KEY from a local .env file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=test-key\nOPENAI_MODEL=gpt-5\n", encoding="utf-8"
    )

    settings = settings_module.get_settings()

    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "gpt-5"
