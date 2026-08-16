"""Application configuration models."""

from pydantic import Field

from backend.models.cv import CVBaseModel


class AISettings(CVBaseModel):
    """Configuration required to create the active AI provider."""

    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=150)
    openai_api_key: str | None = Field(default=None, min_length=1)
