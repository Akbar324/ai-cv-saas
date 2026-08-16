"""Document parsing services."""

from pathlib import Path

from docx import Document

from backend.models.document import ExtractedDocument


class DocumentParsingError(Exception):
    """Raised when an uploaded document cannot be parsed safely."""


def extract_docx(path: Path) -> ExtractedDocument:
    """Extract normalized paragraph text from a DOCX document."""

    if path.suffix.lower() != ".docx":
        raise DocumentParsingError("Expected a .docx file.")

    if not path.exists():
        raise DocumentParsingError(f"Document does not exist: {path}")

    if not path.is_file():
        raise DocumentParsingError(f"Document path is not a file: {path}")

    try:
        document = Document(str(path))
    except Exception as exc:
        raise DocumentParsingError("Unable to open DOCX document.") from exc

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text = "\n".join(paragraphs)

    if not text:
        raise DocumentParsingError("DOCX document contains no extractable text.")

    return ExtractedDocument.from_text(
        path=path,
        file_type="docx",
        text=text,
        paragraph_count=len(paragraphs),
    )
