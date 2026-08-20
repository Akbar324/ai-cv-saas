"""Configured application workflow for CV processing and persistence."""

from pathlib import Path

from backend.models.aws_settings import load_aws_settings
from backend.models.order import Order
from backend.models.settings import load_ai_settings
from backend.services.ai_factory import create_ai_provider
from backend.services.cv_persistence import persist_processed_cv
from backend.services.repository_factory import (
    create_document_repository,
    create_order_repository,
)


def process_and_persist_cv(
    *,
    order: Order,
    source_path: Path,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> Order:
    """Run the configured end-to-end CV persistence workflow."""

    ai_settings = load_ai_settings()
    aws_settings = load_aws_settings()

    provider = create_ai_provider(ai_settings)
    document_repository = create_document_repository(aws_settings)
    order_repository = create_order_repository(aws_settings)

    return persist_processed_cv(
        order=order,
        source_path=source_path,
        provider=provider,
        document_repository=document_repository,
        order_repository=order_repository,
        job_description=job_description,
        additional_customer_information=additional_customer_information,
    )
