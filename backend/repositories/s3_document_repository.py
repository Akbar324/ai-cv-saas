"""Amazon S3 implementation of the document repository."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from backend.repositories.document_repository import (
    DocumentRepository,
    StoredDocument,
    UploadTarget,
)


class S3DocumentRepository(DocumentRepository):
    """Store CV source and generated documents in one private S3 bucket."""

    def __init__(
        self,
        *,
        bucket_name: str,
        client: Any,
    ) -> None:
        if not bucket_name.strip():
            raise ValueError("S3 bucket name must not be empty.")

        self._bucket_name = bucket_name
        self._client = client

    def put_file(
        self,
        *,
        key: str,
        path: Path,
        content_type: str,
    ) -> StoredDocument:
        """Upload one local file to S3."""

        self._validate_key(key)

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise ValueError(f"Document path is not a file: {path}")

        size_bytes = path.stat().st_size

        with path.open("rb") as file:
            self._client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=file,
                ContentType=content_type,
            )

        return StoredDocument(
            key=key,
            content_type=content_type,
            size_bytes=size_bytes,
        )

    def put_text(
        self,
        *,
        key: str,
        content: str,
        content_type: str,
    ) -> StoredDocument:
        """Store one UTF-8 text document in S3."""

        self._validate_key(key)

        body = content.encode("utf-8")

        self._client.put_object(
            Bucket=self._bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

        return StoredDocument(
            key=key,
            content_type=content_type,
            size_bytes=len(body),
        )

    def get_text(self, key: str) -> str:
        """Download one UTF-8 text document from S3."""

        self._validate_key(key)

        response = self._client.get_object(
            Bucket=self._bucket_name,
            Key=key,
        )

        body = response["Body"].read()

        if not isinstance(body, bytes):
            raise TypeError("S3 object body must be bytes.")

        return body.decode("utf-8")

    def download_file(
        self,
        *,
        key: str,
        path: Path,
    ) -> None:
        """Download one S3 object to a local file."""

        self._validate_key(key)

        path.parent.mkdir(parents=True, exist_ok=True)

        self._client.download_file(
            self._bucket_name,
            key,
            str(path),
        )

    def create_upload_target(
        self,
        *,
        key: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int = 900,
    ) -> UploadTarget:
        """Create a size-limited presigned POST upload target."""

        self._validate_key(key)

        if max_size_bytes <= 0:
            raise ValueError("Maximum upload size must be positive.")

        if expires_in_seconds <= 0:
            raise ValueError("Upload expiration must be positive.")

        result = self._client.generate_presigned_post(
            Bucket=self._bucket_name,
            Key=key,
            Fields={
                "Content-Type": content_type,
            },
            Conditions=[
                {
                    "Content-Type": content_type,
                },
                [
                    "content-length-range",
                    1,
                    max_size_bytes,
                ],
            ],
            ExpiresIn=expires_in_seconds,
        )

        return UploadTarget(
            key=key,
            url=result["url"],
            fields=result["fields"],
            expires_in_seconds=expires_in_seconds,
        )

    def delete(self, key: str) -> None:
        """Delete one object from S3."""

        self._validate_key(key)

        self._client.delete_object(
            Bucket=self._bucket_name,
            Key=key,
        )

    def exists(self, key: str) -> bool:
        """Return whether one object currently exists."""

        self._validate_key(key)

        try:
            self._client.head_object(
                Bucket=self._bucket_name,
                Key=key,
            )
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = str(error.get("Code", ""))

            if code in {"404", "NoSuchKey", "NotFound"}:
                return False

            raise

        return True

    @staticmethod
    def _validate_key(key: str) -> None:
        """Reject empty or obviously unsafe S3 object keys."""

        normalized = key.strip()

        if not normalized:
            raise ValueError("S3 object key must not be empty.")

        if normalized.startswith("/"):
            raise ValueError("S3 object key must not start with '/'.")

        if ".." in normalized.split("/"):
            raise ValueError("S3 object key must not contain '..' segments.")
