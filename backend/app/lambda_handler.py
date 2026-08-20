"""AWS Lambda HTTP API entry point."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from backend.models.api import CreateOrderRequest, CreateUploadTargetRequest
from backend.services.cv_workflow import process_uploaded_cv
from backend.services.order_service import create_order, get_order
from backend.services.runtime import get_document_repository, get_order_repository
from backend.services.upload_service import create_source_upload_target


def response(
    status_code: int,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Build an API Gateway HTTP API response."""

    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
        },
        "body": json.dumps(body),
    }


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Route API Gateway HTTP API requests."""

    del context

    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()

    path = event.get("rawPath", "")

    repository = get_order_repository()

    if method == "POST" and path == "/orders":
        return handle_create_order(event, repository)

    if method == "POST" and path.endswith("/upload-url"):
        order_id = path.removeprefix("/orders/").removesuffix("/upload-url").strip("/")

        if not order_id or "/" in order_id:
            return response(404, {"message": "Route not found."})

        return handle_create_upload_target(
            event,
            order_id,
            repository,
        )

    if method == "POST" and path.endswith("/process"):
        order_id = path.removeprefix("/orders/").removesuffix("/process").strip("/")

        if not order_id or "/" in order_id:
            return response(404, {"message": "Route not found."})

        return handle_process_order(
            event,
            order_id,
            repository,
        )

    if method == "GET" and path.startswith("/orders/"):
        order_id = path.removeprefix("/orders/").strip()

        if not order_id or "/" in order_id:
            return response(
                404,
                {"message": "Route not found."},
            )

        return handle_get_order(order_id, repository)

    return response(
        404,
        {"message": "Route not found."},
    )


def handle_create_order(
    event: dict[str, Any],
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders."""

    raw_body = event.get("body")

    if not raw_body:
        return response(
            400,
            {"message": "Request body is required."},
        )

    try:
        payload = json.loads(raw_body)

        if not isinstance(payload, dict):
            raise ValueError

        request = CreateOrderRequest.model_validate(payload)

    except (json.JSONDecodeError, ValueError, ValidationError):
        return response(
            400,
            {"message": "Invalid order request."},
        )

    order = create_order(
        request=request,
        repository=repository,
    )

    return response(
        201,
        order.model_dump(mode="json"),
    )


def handle_get_order(
    order_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle GET /orders/{order_id}."""

    order = get_order(
        order_id=order_id,
        repository=repository,
    )

    if order is None:
        return response(
            404,
            {"message": "Order not found."},
        )

    return response(
        200,
        order.model_dump(mode="json"),
    )


def handle_create_upload_target(
    event: dict[str, Any],
    order_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders/{order_id}/upload-url."""

    order = get_order(
        order_id=order_id,
        repository=repository,
    )

    if order is None:
        return response(404, {"message": "Order not found."})

    raw_body = event.get("body")

    if not raw_body:
        return response(
            400,
            {"message": "Request body is required."},
        )

    try:
        payload = json.loads(raw_body)

        if not isinstance(payload, dict):
            raise ValueError

        request = CreateUploadTargetRequest.model_validate(payload)

        target = create_source_upload_target(
            order=order,
            filename=request.filename,
            content_type=request.content_type,
            document_repository=get_document_repository(),
            order_repository=repository,
        )

    except (json.JSONDecodeError, ValueError, ValidationError):
        return response(
            400,
            {"message": "Invalid upload request."},
        )

    return response(
        200,
        {
            "object_key": target.key,
            "upload_url": target.url,
            "fields": target.fields,
            "expires_in_seconds": target.expires_in_seconds,
        },
    )


def handle_process_order(
    event: dict[str, Any],
    order_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders/{order_id}/process."""

    order = get_order(
        order_id=order_id,
        repository=repository,
    )

    if order is None:
        return response(404, {"message": "Order not found."})

    raw_body = event.get("body")
    payload: dict[str, Any] = {}

    if raw_body:
        try:
            decoded = json.loads(raw_body)

            if not isinstance(decoded, dict):
                raise ValueError

            payload = decoded

        except (json.JSONDecodeError, ValueError):
            return response(
                400,
                {"message": "Invalid processing request."},
            )

    try:
        processed = process_uploaded_cv(
            order=order,
            job_description=payload.get("job_description"),
            additional_customer_information=payload.get(
                "additional_customer_information"
            ),
        )
    except (ValueError, FileNotFoundError) as exc:
        return response(
            400,
            {"message": str(exc)},
        )

    return response(
        200,
        processed.model_dump(mode="json"),
    )
