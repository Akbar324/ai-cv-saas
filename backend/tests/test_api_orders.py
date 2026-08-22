"""Tests for order HTTP API routes."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from backend.app.lambda_handler import lambda_handler
from backend.models.order import Order
from backend.repositories.order_repository import (
    OrderPage,
    OrderRepository,
)


class FakeOrderRepository(OrderRepository):
    """In-memory repository for HTTP API tests."""

    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}

    def create(self, order: Order) -> None:
        self.orders[order.order_id] = order

    def get(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    def update(self, order: Order) -> None:
        self.orders[order.order_id] = order

    def list_by_customer(
        self,
        customer_id: str,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        raise NotImplementedError

    def list_by_order_status(
        self,
        status: Any,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        raise NotImplementedError

    def list_by_processing_status(
        self,
        status: Any,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        raise NotImplementedError

    def list_recent(
        self,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        raise NotImplementedError


@pytest.fixture
def repository(
    monkeypatch: pytest.MonkeyPatch,
) -> FakeOrderRepository:
    repo = FakeOrderRepository()

    monkeypatch.setattr(
        "backend.app.lambda_handler.get_order_repository",
        lambda: repo,
    )

    return repo


def event(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    customer_id: str = "customer-001",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "requestContext": {
            "http": {
                "method": method,
            },
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": customer_id,
                    }
                }
            },
        },
        "rawPath": path,
    }

    if body is not None:
        result["body"] = json.dumps(body)

    return result


def test_post_orders_creates_order(
    repository: FakeOrderRepository,
) -> None:
    result = lambda_handler(
        event(
            "POST",
            "/orders",
            {
                "target_job_title": "Cloud Engineer",
                "target_industry": "Cloud Computing",
            },
        ),
        None,
    )

    assert result["statusCode"] == 201

    payload = json.loads(result["body"])

    assert payload["customer_id"] == "customer-001"
    assert payload["target_job_title"] == "Cloud Engineer"
    assert payload["order_id"].startswith("ord_")

    assert payload["order_id"] in repository.orders


def test_post_orders_rejects_invalid_request(
    repository: FakeOrderRepository,
) -> None:
    result = lambda_handler(
        event(
            "POST",
            "/orders",
            {
                "customer_id": "customer-001",
                "target_job_title": "",
            },
        ),
        None,
    )

    assert result["statusCode"] == 400


def test_get_order_returns_existing_order(
    repository: FakeOrderRepository,
) -> None:
    now = datetime.now(UTC)

    order = Order(
        order_id="ord_test",
        customer_id="customer-001",
        target_job_title="Cloud Engineer",
        created_at=now,
        updated_at=now,
    )

    repository.create(order)

    result = lambda_handler(
        event("GET", "/orders/ord_test"),
        None,
    )

    assert result["statusCode"] == 200

    payload = json.loads(result["body"])

    assert payload["order_id"] == "ord_test"


def test_get_order_returns_404_when_missing(
    repository: FakeOrderRepository,
) -> None:
    result = lambda_handler(
        event("GET", "/orders/does-not-exist"),
        None,
    )

    assert result["statusCode"] == 404


def test_unknown_route_returns_404(
    repository: FakeOrderRepository,
) -> None:
    result = lambda_handler(
        event("GET", "/unknown"),
        None,
    )

    assert result["statusCode"] == 404


def test_create_order_uses_authenticated_customer(
    repository: FakeOrderRepository,
) -> None:
    result = lambda_handler(
        event(
            "POST",
            "/orders",
            {
                "target_job_title": "Cloud Engineer",
            },
            customer_id="cognito-sub-123",
        ),
        None,
    )

    payload = json.loads(result["body"])

    assert result["statusCode"] == 201
    assert payload["customer_id"] == "cognito-sub-123"


def test_customer_cannot_read_another_customers_order(
    repository: FakeOrderRepository,
) -> None:
    now = datetime.now(UTC)

    repository.create(
        Order(
            order_id="ord_private",
            customer_id="customer-owner",
            target_job_title="Cloud Engineer",
            created_at=now,
            updated_at=now,
        )
    )

    result = lambda_handler(
        event(
            "GET",
            "/orders/ord_private",
            customer_id="different-customer",
        ),
        None,
    )

    assert result["statusCode"] == 404
