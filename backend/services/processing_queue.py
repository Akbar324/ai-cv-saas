"""Asynchronous CV processing queue."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from backend.models.order import Order, ProcessingStatus
from backend.repositories.order_repository import OrderRepository


class SQSProcessingQueue:
    """Submit CV processing jobs to Amazon SQS."""

    def __init__(
        self,
        *,
        queue_url: str,
        client: Any,
    ) -> None:
        if not queue_url.strip():
            raise ValueError("Processing queue URL must not be empty.")

        self._queue_url = queue_url
        self._client = client

    def enqueue(
        self,
        *,
        order_id: str,
        job_description: str | None = None,
        additional_customer_information: str | None = None,
    ) -> str:
        """Submit one CV processing job."""

        payload = {
            "order_id": order_id,
            "job_description": job_description,
            "additional_customer_information": (additional_customer_information),
        }

        response = self._client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(payload),
        )

        message_id = response.get("MessageId")

        if not isinstance(message_id, str):
            raise RuntimeError("SQS did not return a message ID.")

        return message_id


def enqueue_order_processing(
    *,
    order: Order,
    queue: SQSProcessingQueue,
    order_repository: OrderRepository,
    job_description: str | None = None,
    additional_customer_information: str | None = None,
) -> str:
    """Queue one order and persist its queued workflow state."""

    if order.processing_status in {
        ProcessingStatus.QUEUED,
        ProcessingStatus.PROCESSING,
    }:
        raise ValueError("Order is already queued or processing.")

    message_id = queue.enqueue(
        order_id=order.order_id,
        job_description=job_description,
        additional_customer_information=(additional_customer_information),
    )

    order.processing_status = ProcessingStatus.QUEUED
    order.updated_at = datetime.now(UTC)

    order_repository.update(order)

    return message_id
