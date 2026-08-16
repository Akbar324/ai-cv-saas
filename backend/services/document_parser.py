"""Document parsing services."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

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


def extract_pdf(path: Path) -> ExtractedDocument:
    """Extract normalized text from a text-based PDF document."""

    if path.suffix.lower() != ".pdf":
        raise DocumentParsingError("Expected a .pdf file.")

    if not path.exists():
        raise DocumentParsingError(f"Document does not exist: {path}")

    if not path.is_file():
        raise DocumentParsingError(f"Document path is not a file: {path}")

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise DocumentParsingError("Unable to open PDF document.") from exc

    pages: list[str] = []

    for page in reader.pages:
        extracted = page.extract_text()

        if extracted:
            normalized = extracted.strip()

            if normalized:
                pages.append(normalized)

    text = "\n".join(pages)

    if not text:
        raise DocumentParsingError(
            "PDF document contains no extractable text. "
            "Scanned or image-only PDFs are not supported yet."
        )

    return ExtractedDocument.from_text(
        path=path,
        file_type="pdf",
        text=text,
        paragraph_count=len(pages),
    )
