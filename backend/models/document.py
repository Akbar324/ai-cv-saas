"""Models for documents uploaded to the AI CV SaaS."""

from pathlib import Path

from pydantic import Field

from backend.models.cv import CVBaseModel


class ExtractedDocument(CVBaseModel):
    """Normalized text extracted from an uploaded customer document."""

    filename: str = Field(min_length=1, max_length=255)
    file_type: str = Field(min_length=1, max_length=20)
    text: str = Field(min_length=1)
    paragraph_count: int = Field(ge=0)
    source_size_bytes: int = Field(ge=0)

    @classmethod
    def from_text(
        cls,
        *,
        path: Path,
        file_type: str,
        text: str,
        paragraph_count: int,
    ) -> "ExtractedDocument":
        """Build an extracted document from normalized parser output."""

        return cls(
            filename=path.name,
            file_type=file_type,
            text=text,
            paragraph_count=paragraph_count,
            source_size_bytes=path.stat().st_size,
        )
