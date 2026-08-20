"""Tests for AWS runtime settings and repository factories."""

from typing import Any

from backend.models.aws_settings import AWSSettings
from backend.repositories.dynamodb_order_repository import (
    DynamoDBOrderRepository,
)
from backend.repositories.s3_document_repository import (
    S3DocumentRepository,
)
from backend.services.repository_factory import (
    create_document_repository,
    create_order_repository,
)


class FakeDynamoDB:
    """Minimal fake DynamoDB resource."""

    def __init__(self) -> None:
        self.last_table_name: str | None = None

    def Table(self, name: str) -> object:  # noqa: N802
        self.last_table_name = name
        return object()


class FakeSession:
    """Minimal fake boto3 session."""

    def __init__(self) -> None:
        self.s3_client = object()
        self.dynamodb = FakeDynamoDB()

    def client(
        self,
        service_name: str,
        **kwargs: Any,
    ) -> object:
        assert service_name == "s3"
        assert kwargs["region_name"] == "me-central-1"
        return self.s3_client

    def resource(
        self,
        service_name: str,
        **kwargs: Any,
    ) -> Any:
        assert service_name == "dynamodb"
        assert kwargs["region_name"] == "me-central-1"
        return self.dynamodb


def aws_settings() -> AWSSettings:
    return AWSSettings(
        _env_file=None,  # type: ignore[call-arg]
        region="me-central-1",
        profile="ai-cv-dev",
        documents_bucket_name="test-documents",
        orders_table_name="test-orders",
    )


def test_create_document_repository_uses_configured_bucket() -> None:
    session = FakeSession()

    repository = create_document_repository(
        aws_settings(),
        session=session,
    )

    assert isinstance(repository, S3DocumentRepository)


def test_create_order_repository_uses_configured_table() -> None:
    session = FakeSession()

    repository = create_order_repository(
        aws_settings(),
        session=session,
    )

    assert isinstance(repository, DynamoDBOrderRepository)
    assert session.dynamodb.last_table_name == "test-orders"


def test_aws_settings_support_local_profile() -> None:
    settings = aws_settings()

    assert settings.profile == "ai-cv-dev"
    assert settings.region == "me-central-1"
