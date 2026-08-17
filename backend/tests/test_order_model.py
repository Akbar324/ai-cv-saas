"""Tests for persistent order domain models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from backend.models.order import (
    Order,
    OrderDocumentReferences,
    OrderStatus,
    PaymentStatus,
    ProcessingStatus,
)


def timestamp() -> datetime:
    return datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


def valid_order() -> Order:
    return Order(
        order_id="order-001",
        customer_id="customer-001",
        target_job_title="Cloud Engineer",
        created_at=timestamp(),
        updated_at=timestamp(),
    )


def test_order_defaults_are_safe() -> None:
    order = valid_order()

    assert order.order_status is OrderStatus.DRAFT
    assert order.processing_status is ProcessingStatus.PENDING
    assert order.payment_status is PaymentStatus.PENDING
    assert order.current_cv_version == 0
    assert order.documents.source_s3_key is None


def test_order_accepts_document_references() -> None:
    order = Order(
        order_id="order-001",
        customer_id="customer-001",
        target_job_title="Cloud Engineer",
        created_at=timestamp(),
        updated_at=timestamp(),
        documents=OrderDocumentReferences(
            source_s3_key="orders/order-001/source/original.docx",
            current_cv_s3_key="orders/order-001/cv/v1.json",
        ),
        current_cv_version=1,
    )

    assert order.documents.source_s3_key == "orders/order-001/source/original.docx"
    assert order.current_cv_version == 1


def test_order_accepts_ai_metadata() -> None:
    order = valid_order()

    order.ai_provider = "gemini"
    order.ai_model = "gemini-3.1-flash-lite"

    assert order.ai_provider == "gemini"
    assert order.ai_model == "gemini-3.1-flash-lite"


def test_order_rejects_negative_cv_version() -> None:
    with pytest.raises(ValidationError):
        Order(
            order_id="order-001",
            customer_id="customer-001",
            target_job_title="Cloud Engineer",
            current_cv_version=-1,
            created_at=timestamp(),
            updated_at=timestamp(),
        )


def test_order_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        Order(
            order_id="order-001",
            customer_id="customer-001",
            target_job_title="Cloud Engineer",
            order_status="made_up_status",  # type: ignore[arg-type]
            created_at=timestamp(),
            updated_at=timestamp(),
        )
