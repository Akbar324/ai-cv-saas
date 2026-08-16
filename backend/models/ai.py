"""Provider-independent models for AI CV processing."""

from pydantic import Field

from backend.models.cv import CanonicalCV, CVBaseModel
from backend.models.document import ExtractedDocument


class CVOptimizationRequest(CVBaseModel):
    """Input required to transform extracted CV content into a canonical CV."""

    document: ExtractedDocument
    target_job_title: str = Field(min_length=1, max_length=150)
    target_industry: str | None = Field(default=None, max_length=150)
    job_description: str | None = Field(default=None, max_length=20_000)
    additional_customer_information: str | None = Field(
        default=None,
        max_length=20_000,
    )


class AIUsage(CVBaseModel):
    """Provider usage metadata returned with an AI operation."""

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class CVOptimizationResult(CVBaseModel):
    """Validated result of one CV optimization operation."""

    cv: CanonicalCV
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=150)
    usage: AIUsage = Field(default_factory=AIUsage)
