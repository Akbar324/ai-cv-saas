"""Runtime dependency construction for deployed application handlers."""

from backend.models.aws_settings import load_aws_settings
from backend.repositories.document_repository import DocumentRepository
from backend.repositories.order_repository import OrderRepository
from backend.services.processing_queue import SQSProcessingQueue
from backend.services.repository_factory import (
    create_document_repository,
    create_order_repository,
    create_processing_queue,
)


def get_order_repository() -> OrderRepository:
    """Create the configured order repository."""

    settings = load_aws_settings()
    return create_order_repository(settings)


def get_document_repository() -> DocumentRepository:
    """Create the configured document repository."""

    settings = load_aws_settings()
    return create_document_repository(settings)


def get_processing_queue() -> SQSProcessingQueue:
    """Create the configured asynchronous processing queue."""

    settings = load_aws_settings()
    return create_processing_queue(settings)
