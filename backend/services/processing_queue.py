"""Asynchronous CV processing queue."""

from __future__ import annotations

import json
from typing import Any


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
