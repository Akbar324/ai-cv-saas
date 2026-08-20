"""Application services for customer CV uploads."""

from datetime import UTC, datetime
from pathlib import Path

from backend.models.order import Order
from backend.repositories.document_repository import (
    DocumentRepository,
    UploadTarget,
)
from backend.repositories.order_repository import OrderRepository

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
PDF_CONTENT_TYPE = "application/pdf"

MAX_SOURCE_CV_SIZE_BYTES = 10 * 1024 * 1024

SUPPORTED_UPLOADS = {
    ".docx": DOCX_CONTENT_TYPE,
    ".pdf": PDF_CONTENT_TYPE,
}


def create_source_upload_target(
    *,
    order: Order,
    filename: str,
    content_type: str,
    document_repository: DocumentRepository,
    order_repository: OrderRepository,
) -> UploadTarget:
    """Create a private direct-upload target for one source CV."""

    suffix = Path(filename).suffix.lower()

    expected_content_type = SUPPORTED_UPLOADS.get(suffix)

    if expected_content_type is None:
        raise ValueError("Only PDF and DOCX CV uploads are supported.")

    if content_type != expected_content_type:
        raise ValueError("Upload content type does not match the file extension.")

    key = f"orders/{order.order_id}/source/original{suffix}"

    target = document_repository.create_upload_target(
        key=key,
        content_type=content_type,
        max_size_bytes=MAX_SOURCE_CV_SIZE_BYTES,
    )

    order.documents.source_s3_key = key
    order.updated_at = datetime.now(UTC)

    order_repository.update(order)

    return target
