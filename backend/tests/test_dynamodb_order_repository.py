"""Tests for the DynamoDB order repository."""

from datetime import UTC, datetime
from typing import Any

from backend.models.order import (
    Order,
    OrderDocumentReferences,
    OrderStatus,
    ProcessingStatus,
)
from backend.repositories.dynamodb_order_repository import (
    DynamoDBOrderRepository,
)


class FakeTable:
    """Minimal fake DynamoDB table for repository tests."""

    def __init__(self) -> None:
        self.last_put: dict[str, Any] | None = None
        self.get_response: dict[str, Any] = {}
        self.query_response: dict[str, Any] = {}
        self.scan_response: dict[str, Any] = {}
        self.last_query: dict[str, Any] | None = None
        self.last_scan: dict[str, Any] | None = None

    def put_item(self, **kwargs: Any) -> dict[str, Any]:
        self.last_put = kwargs
        return {}

    def get_item(self, **kwargs: Any) -> dict[str, Any]:
        return self.get_response

    def query(self, **kwargs: Any) -> dict[str, Any]:
        self.last_query = kwargs
        return self.query_response

    def scan(self, **kwargs: Any) -> dict[str, Any]:
        self.last_scan = kwargs
        return self.scan_response


def sample_order() -> Order:
    timestamp = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)

    return Order(
        order_id="order-001",
        customer_id="customer-001",
        order_status=OrderStatus.HUMAN_REVIEW,
        processing_status=ProcessingStatus.SUCCEEDED,
        target_job_title="Cloud Engineer",
        current_cv_version=1,
        documents=OrderDocumentReferences(
            source_s3_key="orders/order-001/source/original.docx",
            current_cv_s3_key="orders/order-001/cv/v1.json",
        ),
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_serialize_order_flattens_document_references() -> None:
    item = DynamoDBOrderRepository._serialize_order(sample_order())

    assert item["order_id"] == "order-001"
    assert item["source_s3_key"] == ("orders/order-001/source/original.docx")
    assert item["current_cv_s3_key"] == "orders/order-001/cv/v1.json"
    assert "documents" not in item


def test_deserialize_order_rebuilds_document_references() -> None:
    item = DynamoDBOrderRepository._serialize_order(sample_order())

    order = DynamoDBOrderRepository._deserialize_order(item)

    assert order.order_id == "order-001"
    assert order.documents.source_s3_key == ("orders/order-001/source/original.docx")


def test_create_uses_duplicate_protection() -> None:
    table = FakeTable()
    repository = DynamoDBOrderRepository(table)

    repository.create(sample_order())

    assert table.last_put is not None
    assert table.last_put["ConditionExpression"] == ("attribute_not_exists(order_id)")


def test_get_returns_none_when_order_does_not_exist() -> None:
    table = FakeTable()
    repository = DynamoDBOrderRepository(table)

    result = repository.get("missing-order")

    assert result is None


def test_get_returns_deserialized_order() -> None:
    table = FakeTable()
    table.get_response = {
        "Item": DynamoDBOrderRepository._serialize_order(sample_order())
    }

    repository = DynamoDBOrderRepository(table)

    result = repository.get("order-001")

    assert result is not None
    assert result.order_id == "order-001"


def test_list_by_customer_queries_customer_index() -> None:
    table = FakeTable()
    table.query_response = {
        "Items": [DynamoDBOrderRepository._serialize_order(sample_order())]
    }

    repository = DynamoDBOrderRepository(table)

    page = repository.list_by_customer("customer-001")

    assert len(page.items) == 1
    assert table.last_query is not None
    assert table.last_query["IndexName"] == ("customer-created-at-index")
    assert table.last_query["ScanIndexForward"] is False


def test_pagination_token_round_trip() -> None:
    key = {
        "order_id": "order-001",
        "customer_id": "customer-001",
    }

    token = DynamoDBOrderRepository._encode_token(key)
    decoded = DynamoDBOrderRepository._decode_token(token)

    assert decoded == key


def test_list_recent_sorts_scan_results_newest_first() -> None:
    table = FakeTable()

    older = sample_order()
    newer = sample_order().model_copy(
        update={
            "order_id": "order-002",
            "created_at": datetime(
                2026,
                8,
                18,
                13,
                0,
                tzinfo=UTC,
            ),
        }
    )

    table.scan_response = {
        "Items": [
            DynamoDBOrderRepository._serialize_order(older),
            DynamoDBOrderRepository._serialize_order(newer),
        ]
    }

    repository = DynamoDBOrderRepository(table)

    page = repository.list_recent()

    assert page.items[0].order_id == "order-002"
    assert page.items[1].order_id == "order-001"


def test_update_requires_existing_order() -> None:
    table = FakeTable()
    repository = DynamoDBOrderRepository(table)

    repository.update(sample_order())

    assert table.last_put is not None
    assert table.last_put["ConditionExpression"] == ("attribute_exists(order_id)")


def test_list_by_order_status_queries_correct_index() -> None:
    table = FakeTable()
    table.query_response = {"Items": []}

    repository = DynamoDBOrderRepository(table)

    repository.list_by_order_status(OrderStatus.HUMAN_REVIEW)

    assert table.last_query is not None
    assert table.last_query["IndexName"] == ("order-status-created-at-index")
    assert table.last_query["ExpressionAttributeValues"] == {
        ":partition_value": "human_review"
    }


def test_list_by_processing_status_queries_correct_index() -> None:
    table = FakeTable()
    table.query_response = {"Items": []}

    repository = DynamoDBOrderRepository(table)

    repository.list_by_processing_status(
        ProcessingStatus.FAILED,
    )

    assert table.last_query is not None
    assert table.last_query["IndexName"] == ("processing-status-created-at-index")
    assert table.last_query["ExpressionAttributeValues"] == {
        ":partition_value": "failed"
    }


def test_query_returns_opaque_next_token() -> None:
    table = FakeTable()

    table.query_response = {
        "Items": [],
        "LastEvaluatedKey": {
            "order_id": "order-009",
            "customer_id": "customer-001",
            "created_at": "2026-08-18T10:00:00+00:00",
        },
    }

    repository = DynamoDBOrderRepository(table)

    page = repository.list_by_customer("customer-001")

    assert page.next_token is not None

    decoded = DynamoDBOrderRepository._decode_token(page.next_token)

    assert decoded["order_id"] == "order-009"


def test_query_accepts_continuation_token() -> None:
    table = FakeTable()
    table.query_response = {"Items": []}

    repository = DynamoDBOrderRepository(table)

    key = {
        "order_id": "order-009",
        "customer_id": "customer-001",
        "created_at": "2026-08-18T10:00:00+00:00",
    }

    token = DynamoDBOrderRepository._encode_token(key)

    repository.list_by_customer(
        "customer-001",
        next_token=token,
    )

    assert table.last_query is not None
    assert table.last_query["ExclusiveStartKey"] == key


def test_scan_accepts_continuation_token() -> None:
    table = FakeTable()
    table.scan_response = {"Items": []}

    repository = DynamoDBOrderRepository(table)

    key = {
        "order_id": "order-009",
    }

    token = DynamoDBOrderRepository._encode_token(key)

    repository.list_recent(next_token=token)

    assert table.last_scan is not None
    assert table.last_scan["ExclusiveStartKey"] == key


def test_decode_token_rejects_invalid_base64() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="Invalid pagination token",
    ):
        DynamoDBOrderRepository._decode_token("not-valid-base64!")


def test_decode_token_rejects_non_object_payload() -> None:
    import base64

    token = base64.urlsafe_b64encode(b'["not", "an", "object"]').decode("ascii")

    import pytest

    with pytest.raises(
        ValueError,
        match="Invalid pagination token",
    ):
        DynamoDBOrderRepository._decode_token(token)
