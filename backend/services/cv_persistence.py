"""Application orchestration for processing and persisting CV orders."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.models.order import (
    Order,
    OrderStatus,
    ProcessingStatus,
)
from backend.repositories.document_repository import DocumentRepository
from backend.repositories.order_repository import OrderRepository
from backend.services.ai_provider import AIProvider
from backend.services.cv_processing import process_cv

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_CONTENT_TYPE = "application/pdf"
JSON_CONTENT_TYPE = "application/json"


def source_content_type(path: Path) -> str:
    """Return the supported content type for one source CV file."""

    suffix = path.suffix.lower()

    if suffix == ".docx":
        return DOCX_CONTENT_TYPE

    if suffix == ".pdf":
        return PDF_CONTENT_TYPE

    raise ValueError(f"Unsupported source document type: {suffix}")


def _touch_order(order: Order) -> None:
    """Update the order modification timestamp."""

    order.updated_at = datetime.now(UTC)


def persist_processed_cv(
    *,
    order: Order,
    source_path: Path,
    provider: AIProvider,
    document_repository: DocumentRepository,
    order_repository: OrderRepository,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
    existing_source_key: str | None = None,
) -> Order:
    """Persist source CV, process it, persist canonical JSON, and update order."""

    order.processing_status = ProcessingStatus.PROCESSING
    _touch_order(order)
    order_repository.update(order)

    try:
        source_key = (
            f"orders/{order.order_id}/source/original{source_path.suffix.lower()}"
        )

        document_repository.put_file(
            key=source_key,
            path=source_path,
            content_type=source_content_type(source_path),
        )

        result = process_cv(
            path=source_path,
            provider=provider,
            target_job_title=order.target_job_title,
            target_industry=order.target_industry,
            job_description=job_description,
            additional_customer_information=additional_customer_information,
        )

        next_version = order.current_cv_version + 1
        cv_key = f"orders/{order.order_id}/cv/v{next_version}.json"

        document_repository.put_text(
            key=cv_key,
            content=result.cv.model_dump_json(indent=2),
            content_type=JSON_CONTENT_TYPE,
        )

        order.documents.source_s3_key = source_key
        order.documents.current_cv_s3_key = cv_key
        order.current_cv_version = next_version

        order.ai_provider = result.provider
        order.ai_model = result.model

        order.processing_status = ProcessingStatus.SUCCEEDED
        order.order_status = OrderStatus.HUMAN_REVIEW
        _touch_order(order)

        order_repository.update(order)

        return order

    except Exception:
        order.processing_status = ProcessingStatus.FAILED
        _touch_order(order)
        order_repository.update(order)
        raise
