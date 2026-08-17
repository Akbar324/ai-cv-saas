"""Tests for application configuration loading."""

import pytest
from pydantic import ValidationError

from backend.models.settings import AISettings


def test_ai_settings_loads_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-key")

    settings = AISettings(_env_file=None)  # type: ignore[call-arg]

    assert settings.provider == "openai"
    assert settings.model == "test-model"
    assert settings.openai_api_key == "test-secret-key"


def test_ai_settings_does_not_require_openai_key_for_other_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "future-provider")
    monkeypatch.setenv("AI_MODEL", "future-model")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = AISettings(_env_file=None)  # type: ignore[call-arg]

    assert settings.provider == "future-provider"
    assert settings.openai_api_key is None


def test_ai_settings_requires_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("AI_MODEL", "test-model")

    with pytest.raises(ValidationError):
        AISettings(_env_file=None)  # type: ignore[call-arg]


def test_ai_settings_requires_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("AI_MODEL", raising=False)

    with pytest.raises(ValidationError):
        AISettings(_env_file=None)  # type: ignore[call-arg]


def test_explicit_settings_can_be_constructed_without_environment() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="openai",
        model="test-model",
        openai_api_key="test-key",
    )

    assert settings.provider == "openai"
    assert settings.model == "test-model"
