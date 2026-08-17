"""Application service for end-to-end CV processing."""

from pathlib import Path

from backend.models.ai import CVOptimizationRequest, CVOptimizationResult
from backend.models.settings import load_ai_settings
from backend.services.ai_factory import create_ai_provider
from backend.services.ai_provider import AIProvider
from backend.services.document_parser import extract_document


def process_cv(
    *,
    path: Path,
    provider: AIProvider,
    target_job_title: str,
    target_industry: str | None = None,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> CVOptimizationResult:
    """Extract an uploaded CV and optimize it through the supplied AI provider."""

    document = extract_document(path)

    request = CVOptimizationRequest(
        document=document,
        target_job_title=target_job_title,
        target_industry=target_industry,
        job_description=job_description,
        additional_customer_information=additional_customer_information,
    )

    return provider.optimize_cv(request)


def process_cv_with_config(
    *,
    path: Path,
    target_job_title: str,
    target_industry: str | None = None,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> CVOptimizationResult:
    """Process a CV using the AI provider selected by application settings."""

    settings = load_ai_settings()
    provider = create_ai_provider(settings)

    return process_cv(
        path=path,
        provider=provider,
        target_job_title=target_job_title,
        target_industry=target_industry,
        job_description=job_description,
        additional_customer_information=additional_customer_information,
    )
