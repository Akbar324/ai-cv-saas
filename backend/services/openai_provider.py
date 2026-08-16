"""OpenAI implementation of the AI CV optimization provider."""

from __future__ import annotations

from typing import Any

from openai import APIError, OpenAI

from backend.models.ai import (
    AIUsage,
    CVOptimizationRequest,
    CVOptimizationResult,
)
from backend.models.cv import CanonicalCV
from backend.services.ai_provider import AIProvider, AIProviderError

SYSTEM_INSTRUCTIONS = """
You are a professional CV optimization engine.

Transform the customer's source CV into the supplied structured CV schema.

Rules:
- Preserve factual accuracy.
- Improve wording, clarity, relevance, and ATS-friendly terminology.
- Tailor the content to the requested target role.
- Never invent employers, job titles, dates, education, certifications,
  projects, skills, responsibilities, or numerical achievements.
- Do not infer unsupported achievements.
- If information is unavailable, leave optional fields empty or null.
- Keep the output professional, concise, and suitable for a CV.
- Treat the customer's supplied source information as the factual source
  of truth.

Primary rule: Improve expression; never invent evidence.
""".strip()


class OpenAIProvider(AIProvider):
    """CV optimization provider backed by the OpenAI Responses API."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("OpenAI model must not be empty.")

        self._model = model

        if client is not None:
            self._client = client
        else:
            self._client = OpenAI(api_key=api_key)

    def optimize_cv(
        self,
        request: CVOptimizationRequest,
    ) -> CVOptimizationResult:
        """Optimize a customer CV and return validated canonical data."""

        user_input = self._build_user_input(request)

        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=user_input,
                text_format=CanonicalCV,
                store=False,
            )
        except APIError as exc:
            raise AIProviderError("OpenAI request failed.") from exc

        parsed = response.output_parsed

        if parsed is None:
            raise AIProviderError("OpenAI returned no valid structured CV output.")

        usage_data = getattr(response, "usage", None)

        usage = AIUsage(
            input_tokens=getattr(usage_data, "input_tokens", None),
            output_tokens=getattr(usage_data, "output_tokens", None),
            total_tokens=getattr(usage_data, "total_tokens", None),
        )

        return CVOptimizationResult(
            cv=parsed,
            provider="openai",
            model=self._model,
            usage=usage,
        )

    @staticmethod
    def _build_user_input(request: CVOptimizationRequest) -> str:
        """Build provider input from normalized customer information."""

        sections = [
            "SOURCE CV:",
            request.document.text,
            "",
            "TARGET JOB TITLE:",
            request.target_job_title,
        ]

        if request.target_industry:
            sections.extend(
                [
                    "",
                    "TARGET INDUSTRY:",
                    request.target_industry,
                ]
            )

        if request.job_description:
            sections.extend(
                [
                    "",
                    "JOB DESCRIPTION:",
                    request.job_description,
                ]
            )

        if request.additional_customer_information:
            sections.extend(
                [
                    "",
                    "ADDITIONAL CUSTOMER INFORMATION:",
                    request.additional_customer_information,
                ]
            )

        return "\n".join(sections)
