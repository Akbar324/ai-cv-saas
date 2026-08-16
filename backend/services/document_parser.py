"""Document parsing services."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

from backend.models.document import ExtractedDocument

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_TEXT_CHARACTERS = 100_000
SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


class DocumentParsingError(Exception):
    """Raised when an uploaded document cannot be parsed safely."""


def validate_source_document(path: Path) -> None:
    """Validate basic source-document safety constraints."""

    if not path.exists():
        raise DocumentParsingError(f"Document does not exist: {path}")

    if not path.is_file():
        raise DocumentParsingError(f"Document path is not a file: {path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentParsingError(
            f"Unsupported document type: {suffix or 'no extension'}. "
            "Supported types are .docx and .pdf."
        )

    size = path.stat().st_size

    if size > MAX_DOCUMENT_SIZE_BYTES:
        raise DocumentParsingError(
            "Document exceeds the maximum allowed size of 10 MB."
        )


def validate_extracted_text(text: str) -> str:
    """Validate normalized extracted text before downstream processing."""

    normalized = text.strip()

    if not normalized:
        raise DocumentParsingError("Document contains no extractable text.")

    if len(normalized) > MAX_EXTRACTED_TEXT_CHARACTERS:
        raise DocumentParsingError(
            "Extracted document text exceeds the maximum allowed length."
        )

    return normalized


def extract_docx(path: Path) -> ExtractedDocument:
    """Extract normalized paragraph text from a DOCX document."""

    validate_source_document(path)

    if path.suffix.lower() != ".docx":
        raise DocumentParsingError("Expected a .docx file.")

    try:
        document = Document(str(path))
    except Exception as exc:
        raise DocumentParsingError("Unable to open DOCX document.") from exc

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text = validate_extracted_text("\n".join(paragraphs))

    return ExtractedDocument.from_text(
        path=path,
        file_type="docx",
        text=text,
        paragraph_count=len(paragraphs),
    )


def extract_pdf(path: Path) -> ExtractedDocument:
    """Extract normalized text from a text-based PDF document."""

    validate_source_document(path)

    if path.suffix.lower() != ".pdf":
        raise DocumentParsingError("Expected a .pdf file.")

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

    try:
        text = validate_extracted_text("\n".join(pages))
    except DocumentParsingError as exc:
        raise DocumentParsingError(
            "PDF document contains no extractable text or exceeds "
            "the supported text limit. Scanned/image-only PDFs are "
            "not supported yet."
        ) from exc

    return ExtractedDocument.from_text(
        path=path,
        file_type="pdf",
        text=text,
        paragraph_count=len(pages),
    )


def extract_document(path: Path) -> ExtractedDocument:
    """Route a supported document to the correct parser."""

    validate_source_document(path)

    suffix = path.suffix.lower()

    if suffix == ".docx":
        return extract_docx(path)

    if suffix == ".pdf":
        return extract_pdf(path)

    raise DocumentParsingError(
        f"Unsupported document type: {suffix or 'no extension'}. "
        "Supported types are .docx and .pdf."
    )
