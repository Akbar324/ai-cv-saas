"""Google Gemini implementation of the AI CV optimization provider."""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

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
- Never create placeholder facts such as "University not specified".
- Never copy a candidate's personal location into an employer or education
  location unless the source explicitly states that location.
- Do not convert general responsibilities into specialized techniques such
  as root cause analysis, data analysis, process improvement, or technical
  troubleshooting unless supported by the source.
- Only include skills directly supported by the customer's supplied
  information.
- Keep the output professional, concise, and suitable for a CV.
- Treat the customer's supplied source CV and additional customer
  information as the only factual evidence about the candidate.
- The target job title, target industry, and job description are targeting
  signals only. Never treat requirements from the job description as skills,
  experience, achievements, or responsibilities the candidate possesses.
- A listed skill such as AWS or Python does not prove production, hands-on,
  commercial, or project experience unless the source explicitly says so.
- Do not strengthen a factual claim beyond the evidence. For example,
  "AWS" must not become "hands-on AWS environments" unless that experience
  is explicitly supported.
- Do not generate or modify application metadata such as schema_version.

Primary rule: Improve expression; never invent evidence.
""".strip()


def build_gemini_cv_schema() -> dict[str, Any]:
    """Build the Gemini schema using CV content fields only."""

    schema = CanonicalCV.model_json_schema()

    properties = schema.get("properties")

    if isinstance(properties, dict):
        properties.pop("schema_version", None)

    required = schema.get("required")

    if isinstance(required, list):
        schema["required"] = [field for field in required if field != "schema_version"]

    return schema


class GeminiProvider(AIProvider):
    """CV optimization provider backed by the Google Gemini API."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("Gemini model must not be empty.")

        self._model = model

        if client is not None:
            self._client = client
        else:
            self._client = genai.Client(api_key=api_key)

    def optimize_cv(
        self,
        request: CVOptimizationRequest,
    ) -> CVOptimizationResult:
        """Optimize a customer CV and return validated canonical data."""

        user_input = self._build_user_input(request)

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    response_mime_type="application/json",
                    response_json_schema=build_gemini_cv_schema(),
                ),
            )
        except Exception as exc:
            raise AIProviderError("Gemini request failed.") from exc

        response_text = getattr(response, "text", None)

        if not response_text:
            raise AIProviderError("Gemini returned no structured CV output.")

        try:
            payload = json.loads(response_text)

            if not isinstance(payload, dict):
                raise AIProviderError("Gemini returned a non-object CV response.")

            # Application metadata is controlled only by our code.
            payload.pop("schema_version", None)
            payload["schema_version"] = "1.0"

            parsed = CanonicalCV.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise AIProviderError("Gemini returned invalid canonical CV data.") from exc

        usage_metadata = getattr(response, "usage_metadata", None)

        usage = AIUsage(
            input_tokens=getattr(
                usage_metadata,
                "prompt_token_count",
                None,
            ),
            output_tokens=getattr(
                usage_metadata,
                "candidates_token_count",
                None,
            ),
            total_tokens=getattr(
                usage_metadata,
                "total_token_count",
                None,
            ),
        )

        return CVOptimizationResult(
            cv=parsed,
            provider="gemini",
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
