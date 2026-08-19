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
    def delete(self, key: str) -> None:
        """Delete one stored document object."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return whether one object currently exists."""
