"""AWS Lambda HTTP API entry point."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from backend.models.api import (
    CreateOrderRequest,
    CreateUploadTargetRequest,
    ProcessOrderRequest,
)
from backend.models.order import Order
from backend.services.auth import (
    AuthenticationError,
    authenticated_customer_id,
)
from backend.services.order_service import create_order, get_order
from backend.services.processing_queue import enqueue_order_processing
from backend.services.runtime import (
    get_document_repository,
    get_order_repository,
    get_processing_queue,
)
from backend.services.upload_service import create_source_upload_target

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


def error_response(
    status_code: int,
    *,
    message: str,
    error_code: str,
) -> dict[str, Any]:
    """Build a stable structured API error response."""

    return response(
        status_code,
        {
            "message": message,
            "error_code": error_code,
        },
    )


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Route API Gateway HTTP API requests."""

    del context

    try:
        return route_request(event)
    except AuthenticationError:
        return error_response(
            401,
            message="Authentication required.",
            error_code="UNAUTHORIZED",
        )
    except Exception:
        logger.exception("Unhandled API request failure.")

        return error_response(
            500,
            message="Internal server error.",
            error_code="INTERNAL_ERROR",
        )


def owned_order(
    *,
    order_id: str,
    customer_id: str,
    repository: Any,
) -> Order | None:
    """Return an order only when it belongs to the authenticated customer."""

    order = get_order(
        order_id=order_id,
        repository=repository,
    )

    if order is None or order.customer_id != customer_id:
        return None

    return order


def route_request(
    event: dict[str, Any],
) -> dict[str, Any]:
    """Route one authenticated HTTP API request."""

    customer_id = authenticated_customer_id(event)

    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()

    path = event.get("rawPath", "")
    repository = get_order_repository()

    if method == "POST" and path == "/orders":
        return handle_create_order(
            event,
            customer_id,
            repository,
        )

    if method == "POST" and path.endswith("/upload-url"):
        order_id = path.removeprefix("/orders/").removesuffix("/upload-url").strip("/")

        if not order_id or "/" in order_id:
            return route_not_found()

        return handle_create_upload_target(
            event,
            order_id,
            customer_id,
            repository,
        )

    if method == "POST" and path.endswith("/process"):
        order_id = path.removeprefix("/orders/").removesuffix("/process").strip("/")

        if not order_id or "/" in order_id:
            return route_not_found()

        return handle_queue_processing(
            event,
            order_id,
            customer_id,
            repository,
        )

    if method == "GET" and path.startswith("/orders/"):
        order_id = path.removeprefix("/orders/").strip()

        if not order_id or "/" in order_id:
            return route_not_found()

        return handle_get_order(
            order_id,
            customer_id,
            repository,
        )

    return route_not_found()


def route_not_found() -> dict[str, Any]:
    return error_response(
        404,
        message="Route not found.",
        error_code="ROUTE_NOT_FOUND",
    )


def handle_create_order(
    event: dict[str, Any],
    customer_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders."""

    raw_body = event.get("body")

    if not raw_body:
        return error_response(
            400,
            message="Request body is required.",
            error_code="MISSING_BODY",
        )

    try:
        payload = json.loads(raw_body)

        if not isinstance(payload, dict):
            raise ValueError

        request = CreateOrderRequest.model_validate(payload)

    except (json.JSONDecodeError, ValueError, ValidationError):
        return error_response(
            400,
            message="Invalid order request.",
            error_code="INVALID_ORDER_REQUEST",
        )

    order = create_order(
        customer_id=customer_id,
        request=request,
        repository=repository,
    )

    return response(
        201,
        order.model_dump(mode="json"),
    )


def handle_get_order(
    order_id: str,
    customer_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle GET /orders/{order_id}."""

    order = owned_order(
        order_id=order_id,
        customer_id=customer_id,
        repository=repository,
    )

    if order is None:
        return order_not_found()

    return response(
        200,
        order.model_dump(mode="json"),
    )


def order_not_found() -> dict[str, Any]:
    """Avoid revealing whether another customer's order exists."""

    return error_response(
        404,
        message="Order not found.",
        error_code="ORDER_NOT_FOUND",
    )


def handle_create_upload_target(
    event: dict[str, Any],
    order_id: str,
    customer_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders/{order_id}/upload-url."""

    order = owned_order(
        order_id=order_id,
        customer_id=customer_id,
        repository=repository,
    )

    if order is None:
        return order_not_found()

    raw_body = event.get("body")

    if not raw_body:
        return error_response(
            400,
            message="Request body is required.",
            error_code="MISSING_BODY",
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
        return error_response(
            400,
            message="Invalid upload request.",
            error_code="INVALID_UPLOAD_REQUEST",
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


def handle_queue_processing(
    event: dict[str, Any],
    order_id: str,
    customer_id: str,
    repository: Any,
) -> dict[str, Any]:
    """Handle POST /orders/{order_id}/process."""

    order = owned_order(
        order_id=order_id,
        customer_id=customer_id,
        repository=repository,
    )

    if order is None:
        return order_not_found()

    if order.documents.source_s3_key is None:
        return error_response(
            400,
            message="Order has no uploaded source CV.",
            error_code="SOURCE_CV_MISSING",
        )

    raw_body = event.get("body")

    try:
        if raw_body:
            payload = json.loads(raw_body)

            if not isinstance(payload, dict):
                raise ValueError

            request = ProcessOrderRequest.model_validate(payload)
        else:
            request = ProcessOrderRequest()

    except (json.JSONDecodeError, ValueError, ValidationError):
        return error_response(
            400,
            message="Invalid processing request.",
            error_code="INVALID_PROCESSING_REQUEST",
        )

    try:
        message_id = enqueue_order_processing(
            order=order,
            queue=get_processing_queue(),
            order_repository=repository,
            job_description=request.job_description,
            additional_customer_information=(request.additional_customer_information),
        )
    except ValueError as exc:
        return error_response(
            409,
            message=str(exc),
            error_code="ORDER_ALREADY_PROCESSING",
        )

    return response(
        202,
        {
            "order_id": order.order_id,
            "processing_status": "queued",
            "message_id": message_id,
        },
    )
