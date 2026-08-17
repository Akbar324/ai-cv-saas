"""Controlled real-AI smoke test using synthetic CV data only."""

from backend.models.ai import CVOptimizationRequest
from backend.models.document import ExtractedDocument
from backend.models.settings import load_ai_settings
from backend.services.ai_factory import create_ai_provider


def main() -> None:
    settings = load_ai_settings()
    provider = create_ai_provider(settings)

    document = ExtractedDocument(
        filename="synthetic-candidate.docx",
        file_type="docx",
        text="""
Alex Morgan
Dubai, UAE

Quality Engineer
Example Engineering LLC
2021 - Present

- Perform technical inspections of telecom infrastructure.
- Review installation work against engineering standards.
- Coordinate with field teams to resolve quality issues.
- Prepare inspection reports.

Education
Bachelor of Engineering

Skills
Quality Inspection
Telecommunications
Python
AWS
""".strip(),
        paragraph_count=17,
        source_size_bytes=1500,
    )

    request = CVOptimizationRequest(
        document=document,
        target_job_title="Junior Cloud Engineer",
        target_industry="Cloud Computing",
        job_description=(
            "Seeking a junior cloud engineer with AWS knowledge, "
            "basic Python skills, troubleshooting ability, and experience "
            "working in technical environments."
        ),
        additional_customer_information=(
            "The candidate is transitioning toward cloud engineering. "
            "Do not invent cloud production experience."
        ),
    )

    print("Sending synthetic CV to configured AI provider...")
    print(f"Provider: {settings.provider}")
    print(f"Model: {settings.model}")
    print()

    result = provider.optimize_cv(request)

    print("AI processing succeeded.")
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model}")
    print()

    print("Token usage:")
    print(f"  Input:  {result.usage.input_tokens}")
    print(f"  Output: {result.usage.output_tokens}")
    print(f"  Total:  {result.usage.total_tokens}")
    print()

    print("Structured CV:")
    print(result.cv.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
