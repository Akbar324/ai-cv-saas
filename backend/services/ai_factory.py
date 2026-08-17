"""Factory for creating configured AI providers."""

from backend.models.settings import AISettings
from backend.services.ai_provider import AIProvider
from backend.services.gemini_provider import GeminiProvider
from backend.services.openai_provider import OpenAIProvider


class UnsupportedAIProviderError(ValueError):
    """Raised when configuration requests an unsupported AI provider."""


def create_ai_provider(settings: AISettings) -> AIProvider:
    """Create the configured AI provider implementation."""

    provider = settings.provider.strip().lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai.")

        return OpenAIProvider(
            model=settings.model,
            api_key=settings.openai_api_key,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini.")

        return GeminiProvider(
            model=settings.model,
            api_key=settings.gemini_api_key,
        )

    raise UnsupportedAIProviderError(f"Unsupported AI provider: {settings.provider}")
