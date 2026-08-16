"""Canonical CV data models.

These models represent the internal source of truth for CV content.

AI-generated or extracted CV data must validate against these models before
it is persisted, edited, or rendered into customer-facing documents.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CVBaseModel(BaseModel):
    """Base configuration shared by all canonical CV models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class PersonalDetails(CVBaseModel):
    """Candidate contact and professional identity information."""

    full_name: str = Field(min_length=1, max_length=150)
    professional_title: str | None = Field(default=None, max_length=150)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=150)
    linkedin_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)


class TargetRole(CVBaseModel):
    """Role the customer wants the CV optimized for."""

    job_title: str = Field(min_length=1, max_length=150)
    industry: str | None = Field(default=None, max_length=150)
    job_description: str | None = Field(default=None, max_length=20_000)


class WorkExperience(CVBaseModel):
    """One employment record."""

    company: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=150)
    start_date: str | None = Field(default=None, max_length=50)
    end_date: str | None = Field(default=None, max_length=50)
    is_current: bool = False
    responsibilities_or_achievements: list[str] = Field(default_factory=list)


class Education(CVBaseModel):
    """One education record."""

    institution: str = Field(min_length=1, max_length=250)
    qualification: str | None = Field(default=None, max_length=250)
    field_of_study: str | None = Field(default=None, max_length=250)
    location: str | None = Field(default=None, max_length=150)
    start_date: str | None = Field(default=None, max_length=50)
    end_date: str | None = Field(default=None, max_length=50)


class Certification(CVBaseModel):
    """Professional certification or credential."""

    name: str = Field(min_length=1, max_length=250)
    issuer: str | None = Field(default=None, max_length=250)
    issue_date: str | None = Field(default=None, max_length=50)
    expiry_date: str | None = Field(default=None, max_length=50)
    credential_id: str | None = Field(default=None, max_length=150)
    credential_url: str | None = Field(default=None, max_length=500)


class Language(CVBaseModel):
    """Candidate language ability."""

    language: str = Field(min_length=1, max_length=100)
    proficiency: str | None = Field(default=None, max_length=100)


class Project(CVBaseModel):
    """Relevant professional, academic, or portfolio project."""

    name: str = Field(min_length=1, max_length=250)
    description: str | None = Field(default=None, max_length=5_000)
    technologies: list[str] = Field(default_factory=list)
    url: str | None = Field(default=None, max_length=500)


class AdditionalInformation(CVBaseModel):
    """Optional custom section that does not fit the standard CV sections."""

    title: str = Field(min_length=1, max_length=150)
    items: list[str] = Field(default_factory=list)


class CanonicalCV(CVBaseModel):
    """Canonical representation of a customer's CV."""

    schema_version: str = "1.0"

    personal_details: PersonalDetails
    target_role: TargetRole

    professional_summary: str | None = Field(default=None, max_length=5_000)

    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    additional_information: list[AdditionalInformation] = Field(default_factory=list)
