"""Tests for the storage-independent document repository contract."""

import inspect

from backend.repositories.document_repository import (
    DocumentRepository,
    StoredDocument,
)


def test_document_repository_is_abstract() -> None:
    assert inspect.isabstract(DocumentRepository)


def test_document_repository_defines_required_operations() -> None:
    expected = {
        "put_file",
        "put_text",
        "get_text",
        "download_file",
        "create_upload_target",
        "delete",
        "exists",
    }

    assert expected.issubset(DocumentRepository.__abstractmethods__)


def test_stored_document_contains_object_metadata() -> None:
    document = StoredDocument(
        key="orders/order-001/cv/v1.json",
        content_type="application/json",
        size_bytes=1024,
    )

    assert document.key == "orders/order-001/cv/v1.json"
    assert document.content_type == "application/json"
    assert document.size_bytes == 1024
