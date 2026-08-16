"""Tests for document parsing services."""

from pathlib import Path

import pytest
from docx import Document

from backend.services.document_parser import (
    DocumentParsingError,
    extract_docx,
)


def create_docx(path: Path, paragraphs: list[str]) -> Path:
    """Create a small DOCX fixture for parser tests."""

    document = Document()

    for paragraph in paragraphs:
        document.add_paragraph(paragraph)

    document.save(str(path))

    return path


def test_extract_docx_returns_normalized_document(tmp_path: Path) -> None:
    path = create_docx(
        tmp_path / "candidate.docx",
        [
            "Test Candidate",
            "Cloud Engineer",
            "AWS | Python | Terraform",
        ],
    )

    result = extract_docx(path)

    assert result.filename == "candidate.docx"
    assert result.file_type == "docx"
    assert result.paragraph_count == 3
    assert result.source_size_bytes > 0
    assert result.text == ("Test Candidate\nCloud Engineer\nAWS | Python | Terraform")


def test_extract_docx_ignores_empty_paragraphs(tmp_path: Path) -> None:
    path = create_docx(
        tmp_path / "candidate.docx",
        [
            "Candidate Name",
            "",
            "Experience",
        ],
    )

    result = extract_docx(path)

    assert result.paragraph_count == 2
    assert result.text == "Candidate Name\nExperience"


def test_extract_docx_rejects_wrong_extension(tmp_path: Path) -> None:
    path = tmp_path / "candidate.pdf"
    path.write_text("Not really a PDF.", encoding="utf-8")

    with pytest.raises(DocumentParsingError, match=r"Expected a \.docx file"):
        extract_docx(path)


def test_extract_docx_rejects_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.docx"

    with pytest.raises(DocumentParsingError, match="does not exist"):
        extract_docx(path)


def test_extract_docx_rejects_empty_document(tmp_path: Path) -> None:
    path = create_docx(tmp_path / "empty.docx", [])

    with pytest.raises(
        DocumentParsingError,
        match="contains no extractable text",
    ):
        extract_docx(path)
