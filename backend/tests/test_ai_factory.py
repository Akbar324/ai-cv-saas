"""Tests for AI provider factory configuration."""

import pytest

from backend.models.settings import AISettings
from backend.services.ai_factory import (
    UnsupportedAIProviderError,
    create_ai_provider,
)
from backend.services.openai_provider import OpenAIProvider


def test_factory_creates_openai_provider() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="openai",
        model="test-model",
        openai_api_key="test-key",
    )

    provider = create_ai_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_factory_normalizes_provider_name() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider=" OpenAI ",
        model="test-model",
        openai_api_key="test-key",
    )

    provider = create_ai_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_factory_requires_openai_api_key() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="openai",
        model="test-model",
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required",
    ):
        create_ai_provider(settings)


def test_factory_rejects_unsupported_provider() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="future-provider",
        model="test-model",
    )

    with pytest.raises(
        UnsupportedAIProviderError,
        match="Unsupported AI provider",
    ):
        create_ai_provider(settings)


def test_factory_creates_gemini_provider() -> None:
    from backend.services.gemini_provider import GeminiProvider

    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="gemini",
        model="test-model",
        gemini_api_key="test-key",
    )

    provider = create_ai_provider(settings)

    assert isinstance(provider, GeminiProvider)


def test_factory_requires_gemini_api_key() -> None:
    settings = AISettings(  # type: ignore[call-arg]
        _env_file=None,
        provider="gemini",
        model="test-model",
    )

    with pytest.raises(
        ValueError,
        match="GEMINI_API_KEY is required",
    ):
        create_ai_provider(settings)
