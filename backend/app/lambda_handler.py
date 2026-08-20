"""AWS Lambda HTTP API entry point."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from backend.models.api import CreateOrderRequest
from backend.services.order_service import create_order, get_order
from backend.services.runtime import get_order_repository


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
