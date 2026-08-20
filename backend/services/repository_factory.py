"""Factories for configured persistence repositories."""

from __future__ import annotations

from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]

from backend.models.aws_settings import AWSSettings
from backend.repositories.dynamodb_order_repository import (
    DynamoDBOrderRepository,
)
from backend.repositories.s3_document_repository import (
    S3DocumentRepository,
)


def create_aws_session(settings: AWSSettings) -> Any:
    """Create the boto3 session used by runtime repositories."""

    return boto3.Session(
        profile_name=settings.profile,
        region_name=settings.region,
    )


def create_document_repository(
    settings: AWSSettings,
    *,
    session: Any | None = None,
) -> S3DocumentRepository:
    """Create the configured S3 document repository."""

    active_session = session or create_aws_session(settings)

    s3_client = active_session.client(
        "s3",
        region_name=settings.region,
        config=Config(
            signature_version="s3v4",
            s3={
                "addressing_style": "virtual",
            },
        ),
    )

    return S3DocumentRepository(
        bucket_name=settings.documents_bucket_name,
        client=s3_client,
    )


def create_order_repository(
    settings: AWSSettings,
    *,
    session: Any | None = None,
) -> DynamoDBOrderRepository:
    """Create the configured DynamoDB order repository."""

    active_session = session or create_aws_session(settings)

    dynamodb = active_session.resource(
        "dynamodb",
        region_name=settings.region,
    )

    return DynamoDBOrderRepository(dynamodb.Table(settings.orders_table_name))
