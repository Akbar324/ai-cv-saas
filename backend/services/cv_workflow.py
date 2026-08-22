"""Configured application workflow for CV processing and persistence."""

from pathlib import Path

from backend.models.aws_settings import load_aws_settings
from backend.models.order import Order
from backend.models.settings import load_ai_settings
from backend.repositories.document_repository import DocumentRepository
from backend.repositories.order_repository import OrderRepository
from backend.services.ai_factory import create_ai_provider
from backend.services.ai_provider import AIProvider
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


def process_uploaded_cv(
    *,
    order: Order,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> Order:
    """Process a source CV that has already been uploaded to document storage."""

    from pathlib import Path
    from tempfile import TemporaryDirectory

    source_key = order.documents.source_s3_key

    if source_key is None:
        raise ValueError("Order has no uploaded source CV.")

    ai_settings = load_ai_settings()
    aws_settings = load_aws_settings()

    provider = create_ai_provider(ai_settings)
    document_repository = create_document_repository(aws_settings)
    order_repository = create_order_repository(aws_settings)

    if not document_repository.exists(source_key):
        raise FileNotFoundError("Uploaded source CV was not found.")

    suffix = Path(source_key).suffix.lower()

    with TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / f"source{suffix}"

        document_repository.download_file(
            key=source_key,
            path=source_path,
        )

        return persist_processed_cv(
            order=order,
            source_path=source_path,
            provider=provider,
            document_repository=document_repository,
            order_repository=order_repository,
            job_description=job_description,
            additional_customer_information=additional_customer_information,
            existing_source_key=source_key,
        )


def process_uploaded_cv_with_dependencies(
    *,
    order: Order,
    provider: AIProvider,
    document_repository: DocumentRepository,
    order_repository: OrderRepository,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> Order:
    """Process an uploaded source using supplied runtime dependencies."""

    from pathlib import Path
    from tempfile import TemporaryDirectory

    source_key = order.documents.source_s3_key

    if source_key is None:
        raise ValueError("Order has no uploaded source CV.")

    if not document_repository.exists(source_key):
        raise FileNotFoundError("Uploaded source CV was not found.")

    suffix = Path(source_key).suffix.lower()

    with TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / f"source{suffix}"

        document_repository.download_file(
            key=source_key,
            path=source_path,
        )

        return persist_processed_cv(
            order=order,
            source_path=source_path,
            provider=provider,
            document_repository=document_repository,
            order_repository=order_repository,
            job_description=job_description,
            additional_customer_information=(additional_customer_information),
            existing_source_key=source_key,
        )
