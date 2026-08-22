"""SQS-driven CV processing worker."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3  # type: ignore[import-untyped]

from backend.models.aws_settings import load_aws_settings
from backend.models.settings import AISettings
from backend.services.ai_factory import create_ai_provider
from backend.services.cv_workflow import (
    process_uploaded_cv_with_dependencies,
)
from backend.services.repository_factory import (
    create_document_repository,
    create_order_repository,
)
from backend.services.secret_service import get_json_secret

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_record(
    record: dict[str, Any],
) -> None:
    """Process one SQS CV job."""

    body = json.loads(record["body"])

    order_id = body.get("order_id")

    if not isinstance(order_id, str) or not order_id:
        raise ValueError("Processing message has no valid order_id.")

    aws_settings = load_aws_settings()

    session = boto3.Session(
        region_name=aws_settings.region,
    )

    secret_id = os.environ["AI_SECRET_ID"]

    secret = get_json_secret(
        secret_id=secret_id,
        session=session,
        region=aws_settings.region,
    )

    gemini_api_key = secret.get("GEMINI_API_KEY")

    if not gemini_api_key:
        raise RuntimeError("Gemini API key is missing from configured secret.")

    ai_settings = AISettings(
        provider=os.environ.get("AI_PROVIDER", "gemini"),
        model=os.environ["AI_MODEL"],
        gemini_api_key=gemini_api_key,
    )

    provider = create_ai_provider(ai_settings)

    order_repository = create_order_repository(
        aws_settings,
        session=session,
    )

    document_repository = create_document_repository(
        aws_settings,
        session=session,
    )

    order = order_repository.get(order_id)

    if order is None:
        raise ValueError(f"Order not found: {order_id}")

    process_uploaded_cv_with_dependencies(
        order=order,
        provider=provider,
        document_repository=document_repository,
        order_repository=order_repository,
        job_description=body.get("job_description"),
        additional_customer_information=body.get("additional_customer_information"),
    )


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Process SQS records with partial batch failure reporting."""

    del context

    failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        message_id = str(record.get("messageId", ""))

        try:
            process_record(record)
        except Exception:
            logger.exception(
                "CV processing failed for SQS message %s",
                message_id,
            )

            failures.append(
                {
                    "itemIdentifier": message_id,
                }
            )

    return {
        "batchItemFailures": failures,
    }
