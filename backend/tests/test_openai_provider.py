"""Tests for the OpenAI CV optimization provider."""

from types import SimpleNamespace
from typing import Any

import pytest

from backend.models.ai import CVOptimizationRequest
from backend.models.cv import CanonicalCV
from backend.models.document import ExtractedDocument
from backend.services.ai_provider import AIProviderError
from backend.services.openai_provider import OpenAIProvider


class FakeResponses:
    """Fake Responses API used to avoid real network requests."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_kwargs: dict[str, Any] | None = None

    def parse(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return self.response


class FakeOpenAIClient:
    """Minimal fake OpenAI client."""

    def __init__(self, response: Any) -> None:
        self.responses = FakeResponses(response)


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


def canonical_cv() -> CanonicalCV:
    return CanonicalCV.model_validate(
        {
            "personal_details": {
                "full_name": "Candidate Name",
                "professional_title": "Cloud Engineer",
            },
            "target_role": {
                "job_title": "Cloud Engineer",
                "industry": "Cloud Computing",
            },
            "professional_summary": ("Engineer with experience in AWS and Python."),
            "skills": [
                "AWS",
                "Python",
            ],
        }
    )


def test_openai_provider_returns_valid_result() -> None:
    fake_response = SimpleNamespace(
        output_parsed=canonical_cv(),
        usage=SimpleNamespace(
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
        ),
    )

    client = FakeOpenAIClient(fake_response)

    provider = OpenAIProvider(
        model="test-model",
        client=client,
    )

    result = provider.optimize_cv(optimization_request())

    assert result.provider == "openai"
    assert result.model == "test-model"
    assert result.cv.personal_details.full_name == "Candidate Name"
    assert result.usage.input_tokens == 1000
    assert result.usage.output_tokens == 500
    assert result.usage.total_tokens == 1500


def test_openai_provider_disables_response_storage() -> None:
    fake_response = SimpleNamespace(
        output_parsed=canonical_cv(),
        usage=None,
    )

    client = FakeOpenAIClient(fake_response)

    provider = OpenAIProvider(
        model="test-model",
        client=client,
    )

    provider.optimize_cv(optimization_request())

    assert client.responses.last_kwargs is not None
    assert client.responses.last_kwargs["store"] is False


def test_openai_provider_uses_canonical_cv_schema() -> None:
    fake_response = SimpleNamespace(
        output_parsed=canonical_cv(),
        usage=None,
    )

    client = FakeOpenAIClient(fake_response)

    provider = OpenAIProvider(
        model="test-model",
        client=client,
    )

    provider.optimize_cv(optimization_request())

    assert client.responses.last_kwargs is not None
    assert client.responses.last_kwargs["text_format"] is CanonicalCV


def test_openai_provider_sends_targeting_information() -> None:
    fake_response = SimpleNamespace(
        output_parsed=canonical_cv(),
        usage=None,
    )

    client = FakeOpenAIClient(fake_response)

    provider = OpenAIProvider(
        model="test-model",
        client=client,
    )

    provider.optimize_cv(optimization_request())

    assert client.responses.last_kwargs is not None

    user_input = client.responses.last_kwargs["input"]

    assert "Cloud Engineer" in user_input
    assert "Cloud Computing" in user_input
    assert "Seeking AWS and automation experience." in user_input


def test_openai_provider_rejects_missing_structured_output() -> None:
    fake_response = SimpleNamespace(
        output_parsed=None,
        usage=None,
    )

    client = FakeOpenAIClient(fake_response)

    provider = OpenAIProvider(
        model="test-model",
        client=client,
    )

    with pytest.raises(
        AIProviderError,
        match="no valid structured CV output",
    ):
        provider.optimize_cv(optimization_request())


def test_openai_provider_requires_model_name() -> None:
    fake_response = SimpleNamespace(
        output_parsed=canonical_cv(),
        usage=None,
    )

    client = FakeOpenAIClient(fake_response)

    with pytest.raises(
        ValueError,
        match="model must not be empty",
    ):
        OpenAIProvider(
            model="",
            client=client,
        )
