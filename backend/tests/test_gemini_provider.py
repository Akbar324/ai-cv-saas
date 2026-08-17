"""Tests for the Google Gemini CV optimization provider."""

from types import SimpleNamespace
from typing import Any

import pytest

from backend.models.ai import CVOptimizationRequest
from backend.models.cv import CanonicalCV
from backend.models.document import ExtractedDocument
from backend.services.ai_provider import AIProviderError
from backend.services.gemini_provider import GeminiProvider


class FakeModels:
    """Fake Gemini models API."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_kwargs: dict[str, Any] | None = None

    def generate_content(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return self.response


class FakeGeminiClient:
    """Minimal fake Gemini client."""

    def __init__(self, response: Any) -> None:
        self.models = FakeModels(response)


def optimization_request() -> CVOptimizationRequest:
    return CVOptimizationRequest(
        document=ExtractedDocument(
            filename="candidate.docx",
            file_type="docx",
            text=("Candidate Name\nQuality Engineer\nExperience with AWS and Python."),
            paragraph_count=3,
            source_size_bytes=2048,
        ),
        target_job_title="Cloud Engineer",
        target_industry="Cloud Computing",
        job_description="Seeking AWS and automation experience.",
    )


def canonical_cv_json() -> str:
    cv = CanonicalCV.model_validate(
        {
            "personal_details": {
                "full_name": "Candidate Name",
                "professional_title": "Cloud Engineer",
            },
            "target_role": {
                "job_title": "Cloud Engineer",
                "industry": "Cloud Computing",
            },
            "skills": [
                "AWS",
                "Python",
            ],
        }
    )

    return cv.model_dump_json()


def test_gemini_provider_returns_valid_result() -> None:
    fake_response = SimpleNamespace(
        text=canonical_cv_json(),
        usage_metadata=SimpleNamespace(
            prompt_token_count=1000,
            candidates_token_count=500,
            total_token_count=1500,
        ),
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    result = provider.optimize_cv(optimization_request())

    assert result.provider == "gemini"
    assert result.model == "test-model"
    assert result.cv.personal_details.full_name == "Candidate Name"
    assert result.usage.input_tokens == 1000
    assert result.usage.output_tokens == 500
    assert result.usage.total_tokens == 1500


def test_gemini_provider_uses_canonical_json_schema() -> None:
    fake_response = SimpleNamespace(
        text=canonical_cv_json(),
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    provider.optimize_cv(optimization_request())

    assert client.models.last_kwargs is not None

    config = client.models.last_kwargs["config"]

    assert config.response_mime_type == "application/json"
    assert "schema_version" not in config.response_json_schema["properties"]


def test_gemini_provider_sends_targeting_information() -> None:
    fake_response = SimpleNamespace(
        text=canonical_cv_json(),
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    provider.optimize_cv(optimization_request())

    assert client.models.last_kwargs is not None

    contents = client.models.last_kwargs["contents"]

    assert "Cloud Engineer" in contents
    assert "Cloud Computing" in contents
    assert "Seeking AWS and automation experience." in contents


def test_gemini_provider_rejects_missing_structured_output() -> None:
    fake_response = SimpleNamespace(
        text=None,
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    with pytest.raises(
        AIProviderError,
        match="no structured CV output",
    ):
        provider.optimize_cv(optimization_request())


def test_gemini_provider_rejects_invalid_canonical_json() -> None:
    fake_response = SimpleNamespace(
        text='{"unexpected": "data"}',
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    with pytest.raises(
        AIProviderError,
        match="invalid canonical CV data",
    ):
        provider.optimize_cv(optimization_request())


def test_gemini_provider_requires_model_name() -> None:
    fake_response = SimpleNamespace(
        text=canonical_cv_json(),
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    with pytest.raises(
        ValueError,
        match="model must not be empty",
    ):
        GeminiProvider(
            model="",
            client=client,
        )


def test_gemini_cannot_override_schema_version() -> None:
    payload = CanonicalCV.model_validate(
        {
            "personal_details": {
                "full_name": "Candidate Name",
            },
            "target_role": {
                "job_title": "Cloud Engineer",
            },
        }
    ).model_dump()

    payload["schema_version"] = "1.0.0"

    import json

    fake_response = SimpleNamespace(
        text=json.dumps(payload),
        usage_metadata=None,
    )

    client = FakeGeminiClient(fake_response)

    provider = GeminiProvider(
        model="test-model",
        client=client,
    )

    result = provider.optimize_cv(optimization_request())

    assert result.cv.schema_version == "1.0"
