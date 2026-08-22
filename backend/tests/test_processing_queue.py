"""Tests for asynchronous processing queue orchestration."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from backend.models.order import Order, ProcessingStatus
from backend.repositories.order_repository import OrderRepository
from backend.services.processing_queue import (
    SQSProcessingQueue,
    enqueue_order_processing,
)


def sample_order() -> Order:
    now = datetime.now(UTC)

    return Order(
        order_id="order-001",
        customer_id="customer-001",
        target_job_title="Cloud Engineer",
        created_at=now,
        updated_at=now,
    )


def test_enqueue_order_sets_queued_status() -> None:
    order = sample_order()

    queue = Mock(spec=SQSProcessingQueue)
    queue.enqueue.return_value = "message-001"

    repository = Mock(spec=OrderRepository)

    message_id = enqueue_order_processing(
        order=order,
        queue=queue,
        order_repository=repository,
    )

    assert message_id == "message-001"
    assert order.processing_status is ProcessingStatus.QUEUED
    repository.update.assert_called_once_with(order)


@pytest.mark.parametrize(
    "status",
    [
        ProcessingStatus.QUEUED,
        ProcessingStatus.PROCESSING,
    ],
)
def test_duplicate_processing_is_rejected(
    status: ProcessingStatus,
) -> None:
    order = sample_order()
    order.processing_status = status

    queue = Mock(spec=SQSProcessingQueue)
    repository = Mock(spec=OrderRepository)

    with pytest.raises(
        ValueError,
        match="already queued or processing",
    ):
        enqueue_order_processing(
            order=order,
            queue=queue,
            order_repository=repository,
        )

    queue.enqueue.assert_not_called()
    repository.update.assert_not_called()
