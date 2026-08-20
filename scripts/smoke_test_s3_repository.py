"""Controlled live S3 repository smoke test using synthetic data only."""

import os

import boto3  # type: ignore[import-untyped]

from backend.repositories.s3_document_repository import (
    S3DocumentRepository,
)

BUCKET_NAME = "ai-cv-saas-dev-documents-874348038937"
REGION = "me-central-1"
TEST_KEY = "smoke-tests/document-repository/synthetic-cv.json"


def main() -> None:
    profile = os.environ.get("AWS_PROFILE")

    print("AWS profile:", profile or "<default>")
    print("Region:", REGION)
    print("Bucket:", BUCKET_NAME)
    print("Test key:", TEST_KEY)
    print()

    session = boto3.Session(
        profile_name=profile,
        region_name=REGION,
    )

    client = session.client("s3")

    repository = S3DocumentRepository(
        bucket_name=BUCKET_NAME,
        client=client,
    )

    content = '{"candidate":"Synthetic Candidate","purpose":"S3 repository smoke test"}'

    print("Uploading synthetic object...")

    stored = repository.put_text(
        key=TEST_KEY,
        content=content,
        content_type="application/json",
    )

    print("Stored:")
    print("  Key:", stored.key)
    print("  Size:", stored.size_bytes)
    print("  Content type:", stored.content_type)
    print()

    print("Exists after upload:", repository.exists(TEST_KEY))

    downloaded = repository.get_text(TEST_KEY)

    print("Read-back matches:", downloaded == content)

    repository.delete(TEST_KEY)

    print("Deleted test object.")
    print("Exists after delete:", repository.exists(TEST_KEY))


if __name__ == "__main__":
    main()
