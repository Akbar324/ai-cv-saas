"""Tests for the canonical CV data model."""

from typing import Any

import pytest
from pydantic import ValidationError

from backend.models.cv import CanonicalCV


def valid_cv_payload() -> dict[str, Any]:
    """Return a minimal valid canonical CV payload."""

    return {
        "personal_details": {
            "full_name": "Test Candidate",
            "email": "candidate@example.com",
            "location": "Dubai, UAE",
        },
        "target_role": {
            "job_title": "Cloud Engineer",
            "industry": "Cloud Computing",
        },
        "professional_summary": (
            "Cloud-focused engineer with experience in infrastructure, "
            "automation, and production systems."
        ),
        "skills": [
            "AWS",
            "Python",
            "Terraform",
        ],
        "work_experience": [
            {
                "company": "Example Company",
                "job_title": "Quality Engineer",
                "start_date": "2022",
                "end_date": "Present",
                "is_current": True,
                "responsibilities_or_achievements": [
                    "Performed technical quality inspections.",
                    "Supported engineering acceptance activities.",
                ],
            }
        ],
        "education": [
            {
                "institution": "Example University",
                "qualification": "Bachelor's Degree",
                "field_of_study": "Engineering",
            }
        ],
    }


def test_valid_cv_payload_is_accepted() -> None:
    cv = CanonicalCV.model_validate(valid_cv_payload())

    assert cv.personal_details.full_name == "Test Candidate"
    assert cv.target_role.job_title == "Cloud Engineer"
    assert cv.schema_version == "1.0"
    assert len(cv.work_experience) == 1


def test_optional_sections_default_to_empty_lists() -> None:
    cv = CanonicalCV.model_validate(valid_cv_payload())

    assert cv.certifications == []
    assert cv.languages == []
    assert cv.projects == []
    assert cv.additional_information == []


def test_full_name_is_required() -> None:
    payload = valid_cv_payload()
    del payload["personal_details"]["full_name"]

    with pytest.raises(ValidationError):
        CanonicalCV.model_validate(payload)


def test_target_job_title_is_required() -> None:
    payload = valid_cv_payload()
    del payload["target_role"]["job_title"]

    with pytest.raises(ValidationError):
        CanonicalCV.model_validate(payload)


def test_unknown_fields_are_rejected() -> None:
    payload = valid_cv_payload()
    payload["made_up_field"] = "This should never be accepted."

    with pytest.raises(ValidationError):
        CanonicalCV.model_validate(payload)


def test_invalid_boolean_value_is_rejected() -> None:
    payload = valid_cv_payload()
    payload["work_experience"][0]["is_current"] = "definitely"

    with pytest.raises(ValidationError):
        CanonicalCV.model_validate(payload)


def test_assignment_validation_is_enabled() -> None:
    cv = CanonicalCV.model_validate(valid_cv_payload())

    with pytest.raises(ValidationError):
        cv.personal_details.full_name = ""
