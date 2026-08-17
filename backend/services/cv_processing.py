"""Application service for end-to-end CV processing."""

from pathlib import Path

from backend.models.ai import CVOptimizationRequest, CVOptimizationResult
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
    """Extract an uploaded CV and optimize it through the configured AI provider."""

    document = extract_document(path)

    request = CVOptimizationRequest(
        document=document,
        target_job_title=target_job_title,
        target_industry=target_industry,
        job_description=job_description,
        additional_customer_information=additional_customer_information,
    )

    return provider.optimize_cv(request)
