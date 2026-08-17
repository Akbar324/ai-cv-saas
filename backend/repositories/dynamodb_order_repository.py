"""DynamoDB implementation of the order repository."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any

from backend.models.order import Order, OrderStatus, ProcessingStatus
from backend.repositories.order_repository import OrderPage, OrderRepository


class DynamoDBOrderRepository(OrderRepository):
    """Persist order metadata in one DynamoDB table."""

    CUSTOMER_INDEX = "customer-created-at-index"
    ORDER_STATUS_INDEX = "order-status-created-at-index"
    PROCESSING_STATUS_INDEX = "processing-status-created-at-index"

    def __init__(self, table: Any) -> None:
        self._table = table

    def create(self, order: Order) -> None:
        """Persist a new order and fail if the order already exists."""

        self._table.put_item(
            Item=self._serialize_order(order),
            ConditionExpression="attribute_not_exists(order_id)",
        )

    def get(self, order_id: str) -> Order | None:
        """Return one order by ID."""

        response = self._table.get_item(
            Key={"order_id": order_id},
        )

        item = response.get("Item")

        if item is None:
            return None

        return self._deserialize_order(item)

    def update(self, order: Order) -> None:
        """Persist the complete current order state."""

        self._table.put_item(
            Item=self._serialize_order(order),
            ConditionExpression="attribute_exists(order_id)",
        )

    def list_by_customer(
        self,
        customer_id: str,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return one customer's orders newest first."""

        return self._query_index(
            index_name=self.CUSTOMER_INDEX,
            partition_name="customer_id",
            partition_value=customer_id,
            limit=limit,
            next_token=next_token,
        )

    def list_by_order_status(
        self,
        status: OrderStatus,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return orders in one business workflow state."""

        return self._query_index(
            index_name=self.ORDER_STATUS_INDEX,
            partition_name="order_status",
            partition_value=status.value,
            limit=limit,
            next_token=next_token,
        )

    def list_by_processing_status(
        self,
        status: ProcessingStatus,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return orders in one technical processing state."""

        return self._query_index(
            index_name=self.PROCESSING_STATUS_INDEX,
            partition_name="processing_status",
            partition_value=status.value,
            limit=limit,
            next_token=next_token,
        )

    def list_recent(
        self,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return recent orders using a controlled paginated Scan."""

        kwargs: dict[str, Any] = {
            "Limit": limit,
        }

        if next_token:
            kwargs["ExclusiveStartKey"] = self._decode_token(next_token)

        response = self._table.scan(**kwargs)

        orders = [self._deserialize_order(item) for item in response.get("Items", [])]

        orders.sort(
            key=lambda order: order.created_at,
            reverse=True,
        )

        last_evaluated_key = response.get("LastEvaluatedKey")

        return OrderPage(
            items=orders,
            next_token=(
                self._encode_token(last_evaluated_key) if last_evaluated_key else None
            ),
        )

    def _query_index(
        self,
        *,
        index_name: str,
        partition_name: str,
        partition_value: str,
        limit: int,
        next_token: str | None,
    ) -> OrderPage:
        """Query one GSI and return an application pagination token."""

        kwargs: dict[str, Any] = {
            "IndexName": index_name,
            "KeyConditionExpression": f"{partition_name} = :partition_value",
            "ExpressionAttributeValues": {
                ":partition_value": partition_value,
            },
            "ScanIndexForward": False,
            "Limit": limit,
        }

        if next_token:
            kwargs["ExclusiveStartKey"] = self._decode_token(next_token)

        response = self._table.query(**kwargs)

        orders = [self._deserialize_order(item) for item in response.get("Items", [])]

        last_evaluated_key = response.get("LastEvaluatedKey")

        return OrderPage(
            items=orders,
            next_token=(
                self._encode_token(last_evaluated_key) if last_evaluated_key else None
            ),
        )

    @staticmethod
    def _serialize_order(order: Order) -> dict[str, Any]:
        """Convert an Order into DynamoDB-friendly primitives."""

        data = order.model_dump(mode="json")

        documents = data.pop("documents")

        data.update(documents)

        return data

    @staticmethod
    def _deserialize_order(item: dict[str, Any]) -> Order:
        """Convert a DynamoDB item into an Order."""

        payload = dict(item)

        document_fields = {
            "source_s3_key",
            "current_cv_s3_key",
            "preview_s3_key",
            "final_pdf_s3_key",
            "final_docx_s3_key",
        }

        documents = {
            field: payload.pop(field) for field in document_fields if field in payload
        }

        payload["documents"] = documents

        return Order.model_validate(payload)

    @staticmethod
    def _encode_token(key: dict[str, Any]) -> str:
        """Encode a DynamoDB continuation key as an opaque token."""

        raw = json.dumps(
            key,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        return base64.urlsafe_b64encode(raw).decode("ascii")

    @staticmethod
    def _decode_token(token: str) -> dict[str, Any]:
        """Decode an opaque application continuation token."""

        raw = base64.urlsafe_b64decode(token.encode("ascii"))

        value = json.loads(raw.decode("utf-8"))

        if not isinstance(value, dict):
            raise ValueError("Invalid pagination token.")

        return value


def datetime_to_iso(value: datetime) -> str:
    """Return an ISO-8601 timestamp suitable for DynamoDB sorting."""

    return value.isoformat()
