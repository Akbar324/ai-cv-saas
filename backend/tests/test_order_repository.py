"""Tests for the storage-independent order repository contract."""

import inspect

from backend.repositories.order_repository import OrderPage, OrderRepository


def test_order_repository_is_abstract() -> None:
    assert inspect.isabstract(OrderRepository)


def test_order_repository_defines_required_operations() -> None:
    expected = {
        "create",
        "get",
        "update",
        "list_by_customer",
        "list_by_order_status",
        "list_by_processing_status",
        "list_recent",
    }

    assert expected.issubset(OrderRepository.__abstractmethods__)


def test_order_page_defaults_to_no_next_token() -> None:
    page = OrderPage(items=[])

    assert page.items == []
    assert page.next_token is None


def test_order_page_accepts_opaque_next_token() -> None:
    page = OrderPage(
        items=[],
        next_token="opaque-continuation-token",
    )

    assert page.next_token == "opaque-continuation-token"
