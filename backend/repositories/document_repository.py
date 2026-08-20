"""Storage-independent contract for CV documents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredDocument:
    """Metadata describing one stored document object."""

    key: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class UploadTarget:
    """Temporary browser upload target for one document."""

    key: str
    url: str
    fields: dict[str, str]
    expires_in_seconds: int


class DocumentRepository(ABC):
    """Storage-independent persistence contract for CV documents."""

    @abstractmethod
    def put_file(
        self,
        *,
        key: str,
        path: Path,
        content_type: str,
    ) -> StoredDocument:
        """Store one file and return object metadata."""

    @abstractmethod
    def put_text(
        self,
        *,
        key: str,
        content: str,
        content_type: str,
    ) -> StoredDocument:
        """Store one UTF-8 text document and return object metadata."""

    @abstractmethod
    def get_text(self, key: str) -> str:
        """Return one UTF-8 text document."""

    @abstractmethod
    def download_file(
        self,
        *,
        key: str,
        path: Path,
    ) -> None:
        """Download one stored object to a local file."""

    @abstractmethod
    def create_upload_target(
        self,
        *,
        key: str,
        content_type: str,
        max_size_bytes: int,
        expires_in_seconds: int = 900,
    ) -> UploadTarget:
        """Create a temporary direct-upload target."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete one stored document object."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether one object currently exists."""
