"""Tests for the Amazon S3 document repository."""

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from backend.repositories.s3_document_repository import (
    S3DocumentRepository,
)


class FakeS3Client:
    """Minimal fake S3 client for repository tests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}
        self.last_bucket: str | None = None

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.last_bucket = kwargs["Bucket"]

        body = kwargs["Body"]

        if hasattr(body, "read"):
            data = body.read()
        else:
            data = body

        self.objects[kwargs["Key"]] = data
        self.content_types[kwargs["Key"]] = kwargs["ContentType"]

        return {}

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        key = kwargs["Key"]

        return {
            "Body": BytesIO(self.objects[key]),
        }

    def delete_object(self, **kwargs: Any) -> dict[str, Any]:
        self.objects.pop(kwargs["Key"], None)
        return {}

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        key = kwargs["Key"]

        if key not in self.objects:
            raise ClientError(
                {
                    "Error": {
                        "Code": "404",
                        "Message": "Not Found",
                    }
                },
                "HeadObject",
            )

        return {}


def repository() -> tuple[S3DocumentRepository, FakeS3Client]:
    client = FakeS3Client()

    return (
        S3DocumentRepository(
            bucket_name="test-documents-bucket",
            client=client,
        ),
        client,
    )


def test_put_text_stores_utf8_content() -> None:
    repo, client = repository()

    result = repo.put_text(
        key="orders/order-001/cv/v1.json",
        content='{"name":"Candidate"}',
        content_type="application/json",
    )

    assert result.key == "orders/order-001/cv/v1.json"
    assert result.content_type == "application/json"
    assert result.size_bytes > 0

    assert client.objects[result.key] == b'{"name":"Candidate"}'
    assert client.last_bucket == "test-documents-bucket"


def test_get_text_returns_decoded_content() -> None:
    repo, client = repository()

    client.objects["orders/order-001/cv/v1.json"] = b'{"name":"Candidate"}'

    result = repo.get_text("orders/order-001/cv/v1.json")

    assert result == '{"name":"Candidate"}'


def test_put_file_uploads_file_bytes(tmp_path: Path) -> None:
    repo, client = repository()

    path = tmp_path / "candidate.docx"
    path.write_bytes(b"synthetic-docx-content")

    result = repo.put_file(
        key="orders/order-001/source/original.docx",
        path=path,
        content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )

    assert result.size_bytes == len(b"synthetic-docx-content")
    assert (
        client.objects["orders/order-001/source/original.docx"]
        == b"synthetic-docx-content"
    )


def test_delete_removes_object() -> None:
    repo, client = repository()

    key = "orders/order-001/cv/v1.json"
    client.objects[key] = b"content"

    repo.delete(key)

    assert key not in client.objects


def test_exists_returns_true_for_existing_object() -> None:
    repo, client = repository()

    key = "orders/order-001/cv/v1.json"
    client.objects[key] = b"content"

    assert repo.exists(key) is True


def test_exists_returns_false_for_missing_object() -> None:
    repo, _ = repository()

    assert repo.exists("orders/order-001/cv/missing.json") is False


def test_put_file_rejects_missing_file(tmp_path: Path) -> None:
    repo, _ = repository()

    with pytest.raises(FileNotFoundError):
        repo.put_file(
            key="orders/order-001/source/missing.docx",
            path=tmp_path / "missing.docx",
            content_type="application/octet-stream",
        )


@pytest.mark.parametrize(
    "key",
    [
        "",
        "   ",
        "/orders/order-001/cv/v1.json",
        "orders/../secret.json",
    ],
)
def test_repository_rejects_invalid_object_keys(key: str) -> None:
    repo, _ = repository()

    with pytest.raises(ValueError):
        repo.put_text(
            key=key,
            content="test",
            content_type="text/plain",
        )


def test_repository_requires_bucket_name() -> None:
    with pytest.raises(
        ValueError,
        match="bucket name must not be empty",
    ):
        S3DocumentRepository(
            bucket_name="",
            client=FakeS3Client(),
        )
