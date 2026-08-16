"""Tests for provider-independent AI processing models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.models.ai import (
    AIUsage,
    CVOptimizationRequest,
    CVOptimizationResult,
)
from backend.models.cv import CanonicalCV
from backend.models.document import ExtractedDocument


def extracted_document() -> ExtractedDocument:
    return ExtractedDocument(
        filename="candidate.docx",
        file_type="docx",
        text="Candidate Name\nCloud Engineer\nAWS Python Terraform",
        paragraph_count=3,
        source_size_bytes=1024,
    )


def canonical_cv() -> CanonicalCV:
    return CanonicalCV.model_validate(
        {
            "personal_details": {
                "full_name": "Candidate Name",
            },
            "target_role": {
                "job_title": "Cloud Engineer",
            },
            "skills": [
                "AWS",
                "Python",
                "Terraform",
            ],
        }
    )


def test_cv_optimization_request_accepts_valid_input() -> None:
    request = CVOptimizationRequest(
        document=extracted_document(),
        target_job_title="Cloud Engineer",
        target_industry="Cloud Computing",
    )

    assert request.document.filename == "candidate.docx"
    assert request.target_job_title == "Cloud Engineer"


def test_cv_optimization_request_requires_target_job_title() -> None:
    with pytest.raises(ValidationError):
        CVOptimizationRequest(
            document=extracted_document(),
            target_job_title="",
        )


def test_cv_optimization_result_accepts_valid_canonical_cv() -> None:
    result = CVOptimizationResult(
        cv=canonical_cv(),
        provider="openai",
        model="test-model",
        usage=AIUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        ),
    )

    assert result.cv.personal_details.full_name == "Candidate Name"
    assert result.provider == "openai"
    assert result.usage.total_tokens == 150


def test_ai_usage_rejects_negative_token_count() -> None:
    with pytest.raises(ValidationError):
        AIUsage(input_tokens=-1)


def test_extracted_document_remains_immutable_input_shape() -> None:
    request = CVOptimizationRequest(
        document=extracted_document(),
        target_job_title="Cloud Engineer",
    )

    assert isinstance(request.document.text, str)
    assert Path(request.document.filename).suffix == ".docx"
