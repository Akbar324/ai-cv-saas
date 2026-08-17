"""Application configuration models."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Configuration required to create the active AI provider."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_",
        extra="ignore",
        case_sensitive=False,
    )

    provider: str = Field(
        min_length=1,
        max_length=100,
    )
    model: str = Field(
        min_length=1,
        max_length=150,
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        min_length=1,
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
        min_length=1,
    )


def load_ai_settings() -> AISettings:
    """Load and validate AI configuration from the environment."""

    return AISettings()  # type: ignore[call-arg]
